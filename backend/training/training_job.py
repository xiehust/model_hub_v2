from sagemaker.estimator import Estimator
from sagemaker.pytorch import PyTorch
from datetime import datetime
import yaml,json
import sagemaker
import shortuuid
import boto3
import logging
from typing import Annotated, Sequence, TypedDict, Dict, Optional,List, Any,TypedDict
from pydantic import BaseModel,Field
import sys
sys.path.append('./')
from logger_config import setup_logger
from training.helper import prepare_dataset_info,to_datetime_string,list_s3_objects
from model.data_model import JobInfo
from core.get_factory_config import get_model_path_by_name
import dotenv
import os
dotenv.load_dotenv()

logger = setup_logger('training_job.py', log_file='processing_engine.log', level=logging.INFO)
BASE_CONFIG = './LLaMA-Factory/examples/train_qlora/llama3_lora_sft_awq.yaml'
region_name = 'us-west-2'
boto_sess = boto3.Session(
    profile_name=os.environ.get('profile','default'),
    region_name=os.environ.get('region')
)

sagemaker_session =  sagemaker.session.Session(boto_session=boto_sess) #sagemaker.session.Session()
region = sagemaker_session.boto_region_name
default_bucket = sagemaker_session.default_bucket()
logger.info(default_bucket)

role = os.environ.get('role')


def fetch_log(log_group_name:str='/aws/sagemaker/TrainingJobs',log_stream_name:str=None):
    # 获取日志组中的所有日志流
    logs_client = boto_sess.client('logs', region_name=region)
    response = logs_client.describe_log_streams(
        logGroupName=log_group_name,
    )
    log_streams = response['logStreams']
    results = []
    # 遍历每个日志流并检索其日志事件
    for log_stream in log_streams:
        stream_name = log_stream['logStreamName']
        if stream_name and stream_name.startswith(log_stream_name):
            logger.info(stream_name)
            response = logs_client.get_log_events(
                logGroupName=log_group_name,
                logStreamName=stream_name
            )
            events = response['events']
            for event in events:
                timestamp = to_datetime_string(event['timestamp']/1000)
                message = event['message']
                results.append(f'{timestamp}: {message}')
                # print(f'{timestamp}: {message}')
    return results
                
                
class TrainingJobExcutor(BaseModel):
    estimator:Any = None
    job_run_name:str = None #SageMaker Training job name
    job_id:str = None
    output_s3_path:str = None
    def __init__(self,*args, **kwargs):
        super().__init__(*args, **kwargs)

        
    def create_training_yaml(self,data_keys:List[str],
                             per_device_train_batch_size:int,
                             gradient_accumulation_steps:int,
                             cutoff_len:int,
                             num_train_epochs:float,
                             warmup_steps:int,
                             max_samples:int,
                             model_id:str,
                             lora_target:str,
                             base_config:str):
        
        with open(base_config) as f:
            doc = yaml.safe_load(f)

        doc['output_dir'] ='/tmp/finetuned_model'
        doc['per_device_train_batch_size'] =per_device_train_batch_size
        doc['gradient_accumulation_steps'] =gradient_accumulation_steps
        doc['lora_target'] = lora_target
        doc['cutoff_len'] = int(cutoff_len)
        doc['num_train_epochs'] = float(num_train_epochs)
        doc['warmup_steps'] = int(warmup_steps)

        #实验时间，只选取前200条数据做训练
        doc['max_samples'] = int(max_samples)
        #数据集
        doc['dataset'] = ','.join(data_keys)
        uuid = shortuuid.uuid()
        sg_config = f'sg_config_qlora_{uuid}.yaml'
        with open(f'./LLaMA-Factory/{sg_config}', 'w') as f:
            yaml.safe_dump(doc, f)
        logger.info(f'save {sg_config}')
        # config lora merge
        sg_lora_merge_config = f'sg_config_lora_merge_{uuid}.yaml'
        doc['model_name_or_path'] = model_id
        doc['adapter_name_or_path'] ='/tmp/finetuned_model'
        doc['export_dir'] ='/tmp/finetuned_model_merged'
        with open(f'./LLaMA-Factory/{sg_lora_merge_config}', 'w') as f:
            yaml.safe_dump(doc, f)
        
        return sg_config,sg_lora_merge_config


    def create_single_qlora_training(self,
                                     model_id:str,
                                     sg_config:str,
                                     sg_lora_merge_config:str,
                                     instance_type:str ,
                                     training_input_path:str=None):
        instance_count = 1
        max_time = 3600*24
        
        base_model_name = model_id.split('/')[-1]
        base_job_name = base_model_name
        
        output_s3_path = f's3://{default_bucket}/{base_job_name}/{self.job_id}/'
        environment = {
            'NODE_NUMBER':str(instance_count),
            "s3_data_paths":f"{training_input_path}",
            # "merge_lora":"0",
            "sg_config":sg_config,
            # "sg_lora_merge_config":sg_lora_merge_config,
            'OUTPUT_MODEL_S3_PATH': output_s3_path # destination
        }
        
        self.output_s3_path = output_s3_path
        self.estimator = PyTorch(entry_point='entry_single_lora.py',
                                    source_dir='./LLaMA-Factory/',
                                    role=role,
                                    sagemaker_session=sagemaker_session,
                                    base_job_name=base_job_name,
                                    environment=environment,
                                    framework_version='2.2.0',
                                    py_version='py310',
                                    script_mode=True,
                                    instance_count=instance_count,
                                    instance_type=instance_type,
                                    enable_remote_debug=True,
                                    # keep_alive_period_in_seconds=600,
                                    max_run=max_time)
        
        
    
    def _create_sft_lora(self,
                         dataset_info:Dict[str,Any],
                instance_type:str ,
               data_keys:List[str],
               model_id:str,
               per_device_train_batch_size:int,
               gradient_accumulation_steps:int,
               lora_target:str,
               cutoff_len:int,
               num_train_epochs:float,
               warmup_steps:int,
               max_samples:int,
               quant_type:str,
               training_input_path:str,
               base_config:str):
        prepare_dataset_info(dataset_info)
        sg_config, sg_lora_merge_config = self.create_training_yaml(data_keys=data_keys,
                                                                    per_device_train_batch_size=per_device_train_batch_size,
                                                                    gradient_accumulation_steps=gradient_accumulation_steps,
                                                                    cutoff_len=cutoff_len,
                                                                    num_train_epochs=num_train_epochs,
                                                                    warmup_steps=warmup_steps,
                                                                    max_samples=max_samples,
                                                                    model_id = model_id,
                                                                    lora_target=lora_target,
                                                                    base_config =base_config)
        if quant_type in ['4','8']:
            self.create_single_qlora_training(sg_config=sg_config,
                                                           model_id=model_id,
                                                           sg_lora_merge_config=sg_lora_merge_config,
                                                           training_input_path= training_input_path,
                                                            instance_type=instance_type)
        else:
            logger.info(f"to do: create none lora training")
    def create(self):
        from core.jobs import sync_get_job_by_id
        jobinfo=sync_get_job_by_id(self.job_id)
        logger.info(f"jobinfo of {self.job_id}:{jobinfo}")
        job_payload = jobinfo.job_payload
        
        
        logger.info(job_payload)
        
        s3_data_path=job_payload.get('s3_data_path')
        

        dataset_info = {}
        # 如果指定了s3路径
        if s3_data_path:
            dataset_info_str = job_payload.get('dataset_info')
            dataset_info = json.loads(dataset_info_str)
            s3_datakeys = list(dataset_info.keys()) if dataset_info else []
            
            # 去掉末尾的反斜杠，因为training script 里会添加
            s3_data_path = s3_data_path[:-1] if s3_data_path[-1] == '/' else s3_data_path
        
        data_keys = job_payload.get('dataset',[])+s3_datakeys
        
        if job_payload['training_stage'] == 'sft' and job_payload['finetuning_method'] == 'lora':
            self._create_sft_lora(dataset_info=dataset_info,
                        instance_type=job_payload['instance_type'],
                        data_keys=data_keys,
                        model_id=get_model_path_by_name(job_payload['model_name']),
                        per_device_train_batch_size = job_payload['batch_size'],
                        gradient_accumulation_steps = job_payload['grad_accu'],
                        lora_target = 'all',
                        training_input_path = s3_data_path,
                        quant_type = job_payload['quant_type'],
                        cutoff_len=job_payload['cutoff_length'],
                        num_train_epochs = job_payload['epoch'],
                        warmup_steps = job_payload['warmup_steps'],
                        max_samples = job_payload['max_samples'],
                        base_config =BASE_CONFIG,
                        )
            return True,'create job success'
        else:
            logger.warn('not supported yet')
            return False, 'type of job not supported yet'
        
    def run(self) -> bool:
        from core.jobs import update_job_run_name_by_id

        if not self.estimator:
            logger.error('estimator is None')
            return False
        self.estimator.fit(wait=False)
        logger.info('---fit----')
        self.job_run_name = self.estimator.latest_training_job.job_name
        
        # save the training job name to db
        update_job_run_name_by_id(self.job_id,self.job_run_name,self.output_s3_path)
        print(f"Training job name: {self.job_run_name},output_s3_path:{self.output_s3_path}")
        self.estimator.logs()
    
    def stop(self) -> bool:
        if not self.estimator:
            logger.error('estimator is None')
            return False
        self.estimator.stop()
        return True
            
        
    
if __name__ == "__main__":
    datasetinfo = {'ruozhiba':{
                        'file_name':'ruozhiba.json',
                        "columns": {
                        "prompt": "instruction",
                        "query": "input",
                        "response": "output",
                }   
                }}
    
    # excutor = TrainingJobExcutor(job_id='04315aa5-316e-4694-8c46-4725dde9c5a5')

    # excutor.create()
    # excutor.run()
    fetch_log(log_stream_name='Meta-Llama-3-8B-Instruct-2024-07-07-15-47-39-934')
    
    

