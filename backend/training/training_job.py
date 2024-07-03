from sagemaker.estimator import Estimator
from sagemaker.pytorch import PyTorch
from datetime import datetime
import yaml,json
import sagemaker
from typing import Generator, Optional, Union, Dict, List, Any
import shortuuid
import boto3
import threading

region_name = 'us-west-2'
boto_sess = boto3.Session(
    profile_name='4344',
    region_name=region_name
)

sagemaker_session =  sagemaker.session.Session(boto_session=boto_sess) #sagemaker.session.Session()
region = sagemaker_session.boto_region_name
default_bucket = sagemaker_session.default_bucket()
role = 'arn:aws:iam::434444145045:role/notebook-hyperpod-ExecutionRole-xHaRX2L05qHQ'


def fetch_log(log_group_name:str,log_stream_name:str=None):
    # 获取日志组中的所有日志流
    logs_client = boto_sess.client('logs', region_name=region)
    response = logs_client.describe_log_streams(
        logGroupName=log_group_name
    )
    log_streams = response['logStreams']

    # 遍历每个日志流并检索其日志事件
    for log_stream in log_streams:
        stream_name = log_stream['logStreamName']
        response = logs_client.get_log_events(
            logGroupName=log_group_name,
            logStreamName=stream_name
        )
        events = response['events']
        for event in events:
            timestamp = event['timestamp']
            message = event['message']
            print(f'{timestamp}: {message}')
    


def update_dataset_info(data_info:Dict[str,Any]):
    file_name = './LLaMA-Factory/data/dataset_info.json'
    with open(file_name) as f:
        datainfo = json.load(f)
        for key in list(data_info.keys()):
            datainfo[key] = data_info[key]
    with open('./LLaMA-Factory/data/dataset_info.json','w') as f:
        json.dump(fp=f,obj=datainfo)
    print('save dataset_info.json')
        
def create_training_yaml(data_keys:List[str],model_id:str,base_config:str):
    
    with open(base_config) as f:
        doc = yaml.safe_load(f)
    # 如果是用SageMaker则使用以下模型文件路径
    # doc['output_dir'] ='/tmp/finetuned_model'
    doc['per_device_train_batch_size'] =1
    doc['gradient_accumulation_steps'] =8
    # doc['lora_target'] = 'all'
    doc['cutoff_len'] = 2048
    doc['num_train_epochs'] = 5.0
    doc['warmup_steps'] = 10

    #实验时间，只选取前200条数据做训练
    doc['max_samples'] = 200 
    #数据集
    doc['dataset'] = ','.join(data_keys)
    uuid = shortuuid.uuid()
    sg_config = f'sg_config_qlora_{uuid}.yaml'
    with open(f'./LLaMA-Factory/{sg_config}', 'w') as f:
        yaml.safe_dump(doc, f)
    print(f'save {sg_config}')
    # config lora merge
    sg_lora_merge_config = f'sg_config_lora_merge_{uuid}.yaml'
    doc['model_name_or_path'] = model_id
    doc['adapter_name_or_path'] ='/tmp/finetuned_model'
    doc['export_dir'] ='/tmp/finetuned_model_merged'
    with open(f'./LLaMA-Factory/{sg_lora_merge_config}', 'w') as f:
        yaml.safe_dump(doc, f)
    
    return sg_config,sg_lora_merge_config


def create_single_qlora_training(sg_config:str,sg_lora_merge_config:str,training_input_path:str=None):
    instance_count = 1
    instance_type = 'ml.g5.2xlarge' 
    max_time = 3600*24

    # Get the current time
    current_time = datetime.now()

    # wandb.sagemaker_auth(path="./")
    # Format the current time as a string
    formatted_time = current_time.strftime("%Y%m%d%H%M%S")
    print(formatted_time)

    base_job_name = 'llama3-8b-qlora-finetune'
    environment = {
        'NODE_NUMBER':str(instance_count),
        "s3_data_paths":f"{training_input_path}",
        # "merge_lora":"0",
        "sg_config":sg_config,
        # "sg_lora_merge_config":sg_lora_merge_config,
        'OUTPUT_MODEL_S3_PATH': f's3://{default_bucket}/llama3-8b-qlora/', # destination
    }

    estimator = PyTorch(entry_point='entry_single_lora.py',
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
    return estimator
    
if __name__ == "__main__":
    datasetinfo = {'ruozhiba':{
                        'file_name':'ruozhiba.json',
                        "columns": {
                        "prompt": "instruction",
                        "query": "input",
                        "response": "output",
                }   
                }}
    update_dataset_info(datasetinfo)
    print(default_bucket)
    sg_config, sg_lora_merge_config = create_training_yaml(data_keys=['ruozhiba_gpt4'],
                                         model_id = 'unsloth/llama-3-8b-Instruct',
                                         base_config ='./LLaMA-Factory/examples/train_qlora/llama3_lora_sft_awq.yaml'
                                         )
    estimator = create_single_qlora_training(sg_config,sg_lora_merge_config)
    estimator.fit(wait=False)
    print('---fit----')
    estimator.logs()
    # training_job_name = estimator.latest_training_job.name
    # attached_estimator = Estimator.attach(training_job_name)
    
    

