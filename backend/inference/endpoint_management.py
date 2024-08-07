import time
import uuid
import sys
sys.path.append('../')
import json
import os
import logging
from typing import Annotated, Sequence, TypedDict, Dict, Optional,List, Any,TypedDict

from model.data_model import *
from db_management.database import DatabaseWrapper
from datetime import datetime
from training.jobs import sync_get_job_by_id
from utils.config import boto_sess,role,default_bucket,sagemaker_session,DEFAULT_ENGINE,DEFAULT_REGION
from utils.get_factory_config import get_model_path_by_name
from sagemaker import image_uris, Model
import sagemaker
from logger_config import setup_logger
import threading
database = DatabaseWrapper()
logger = setup_logger('endpoint_management.py', log_file='deployment.log', level=logging.INFO)

endpoints_lock = threading.Lock()
thread_pool = {}
def check_deployment_status(endpoint_name:str):
    logger.info('a thread start')
    while True:
        status  = get_endpoint_status(endpoint_name)
        if status == EndpointStatus.CREATING:
            time.sleep(30)
        else:
            with endpoints_lock:
                thread_pool.pop(endpoint_name)
            logger.info('a thread exit')
            return True


def get_endpoint_status(endpoint_name:str) ->EndpointStatus:
    client = boto_sess.client('sagemaker')
    try:
        resp = client.describe_endpoint(EndpointName=endpoint_name)
        # logger.info(resp)
        status = resp['EndpointStatus']
        if status == 'InService':
            logger.info("Deployment completed successfully.")
            print("Deployment completed successfully.")
            database.update_endpoint_status(
                endpoint_name=endpoint_name,
                endpoint_status=EndpointStatus.INSERVICE
            )
            return EndpointStatus.INSERVICE
        elif status in ['Failed']:
            logger.info("Deployment failed or is being deleted.")
            database.update_endpoint_status(
                endpoint_name=endpoint_name,
                endpoint_status=EndpointStatus.FAILED
            )
            return EndpointStatus.FAILED
        elif status in ['Creating']:
            database.update_endpoint_status(
                endpoint_name=endpoint_name,
                endpoint_status=EndpointStatus.CREATING
            )
            return EndpointStatus.CREATING
            
        else:
            return EndpointStatus.NOTFOUND
    except Exception as e:
        logger.error(e)
        return EndpointStatus.NOTFOUND
        
def delete_endpoint(endpoint_name:str) ->bool:
    client = boto_sess.client('sagemaker')
    try:
        # database.update_endpoint_status(
        #         endpoint_name=endpoint_name,
        #         endpoint_status=EndpointStatus.TERMINATED,
        #         endpoint_delete_time= datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        #     )
        database.delete_endpoint(endpoint_name=endpoint_name)
        client.delete_endpoint(EndpointName=endpoint_name)
        client.delete_endpoint_config(EndpointConfigName=endpoint_name)
        client.delete_model(ModelName=endpoint_name)
        return True
    except Exception as e:
        logger.error(e)
        return True
        
# 如果job_id="",则使用model_name原始模型
def deploy_endpoint(job_id:str,engine:str,instance_type:str,quantize:str,enable_lora:bool,model_name:str) -> Dict[bool,str]:
    if not job_id == 'N/A(Not finetuned)':
        jobinfo = sync_get_job_by_id(job_id)
        if not jobinfo.job_status == JobStatus.SUCCESS:
            return CommonResponse(response_id=job_id,response={"error": "job is not ready to deploy"})
        # 如果是lora模型，则使用merge之后的路径
        if jobinfo.job_payload['finetuning_method'] == 'lora':
            model_path = jobinfo.output_s3_path + 'finetuned_model_merged/'
        else:
            model_path = jobinfo.output_s3_path + 'finetuned_model/'
        model_name = jobinfo.job_payload["model_name"]
    elif not model_name == '':
        model_path = get_model_path_by_name(model_name)
    else:
        return CommonResponse(response_id=job_id,response={"error": "no model_name is provided"})
    logger.info(f"deploy endpoint with model_path:{model_path}")
    
    # Fetch the uri of the LMI container that supports vLLM, LMI-Dist, HuggingFace Accelerate backends
    if engine == 'trt-llm':
        lmi_image_uri = image_uris.retrieve(framework="djl-tensorrtllm", version="0.29.0", region=DEFAULT_REGION)
    else:
        lmi_image_uri = image_uris.retrieve(framework="djl-lmi", version="0.29.0", region=DEFAULT_REGION)

    env={
        "HF_MODEL_ID": model_path,
        "OPTION_ROLLING_BATCH":  engine,
        "TENSOR_PARALLEL_DEGREE": "max",
         "HUGGING_FACE_HUB_TOKEN":os.environ.get('HUGGING_FACE_HUB_TOKEN'),
    }
    if enable_lora:
        env['OPTION_ENABLE_LORA'] = True
        
    if engine == 'trt-llm':
        env['OPTION_MAX_NUM_TOKENS'] = '50000'
        env['OPTION_ENABLE_KV_CACHE_REUSE'] = "true"
        
    #量化设置
    if engine == 'scheduler' and quantize in ['bitsandbytes8','bitsandbytes4']:
        env['OPTION_QUANTIZE'] = quantize
    elif engine == 'llm-dist' and  quantize in ['awq','gptq']:
        env['OPTION_QUANTIZE'] = quantize
    elif engine == 'trt-llm' and  quantize in ['awq','smoothquant']:
        env['OPTION_QUANTIZE'] = quantize
    
    #patches   
    ##Mistral-7B 在g5.2x下kv cache不能超过12k，否则会报错  
    if engine == 'vllm' and instance_type.endswith('2xlarge'):
        if model_name.startswith('Mistral-7B'): 
            env['OPTION_MAX_MODEL_LEN'] = '12288' 

    
    create_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    endpoint_name = sagemaker.utils.name_from_base(model_name).replace('.','-').replace('_','-')

    # Create the SageMaker Model object. In this example we let LMI configure the deployment settings based on the model architecture  
    model = Model(
            image_uri=lmi_image_uri,
            role=role,
            name=endpoint_name,
            sagemaker_session=sagemaker_session,
            env=env,
    )
    try:
        model.deploy(
            instance_type= instance_type,
            initial_instance_count=1,
            endpoint_name=endpoint_name,
            wait=False,
            accept_eula=True,
            container_startup_health_check_timeout=1800
        )
        database.create_endpoint(job_id= job_id,
                                 model_name= model_name,
                                 model_s3_path= model_path,
                                 instance_type= instance_type,
                                 endpoint_name= endpoint_name,
                                 endpoint_create_time= create_time,
                                 endpoint_delete_time= None,
                                 extra_config= None,
                                 engine=engine,
                                 enable_lora=enable_lora,
                                 endpoint_status = EndpointStatus.CREATING
                                 )
    except Exception as e:
        logger.error(f"create_endpoint:{e}")
        return False,''
    
    return True,endpoint_name

def list_endpoints(request:ListEndpointsRequest) -> Dict[EndpointInfo,int]:
    logger.info(f"thread pool:{thread_pool}")
    results = database.list_endpoints(query_terms=request.query_terms,page_size=request.page_size,page_index=request.page_index)
    info =  [EndpointInfo(job_id=job_id,
                            endpoint_name=endpoint_name,
                            model_name=model_name,
                            engine=engine,
                            enable_lora=enable_lora,
                            instance_type=instance_type,
                            instance_count=instance_count,
                            model_s3_path=model_s3_path,
                            endpoint_status=endpoint_status,
                            endpoint_create_time=endpoint_create_time,
                            endpoint_delete_time=endpoint_delete_time,
                            extra_config=extra_config
                    ) 
            for _,job_id,endpoint_name,model_name,engine,enable_lora,instance_type,instance_count,model_s3_path,endpoint_status,endpoint_create_time,endpoint_delete_time,extra_config in results]
    
    count = database.count_endpoints(query_terms=request.query_terms)
    
    #启动一个线程来更新状态
    for endpoint_info in info:
        if endpoint_info.endpoint_status == EndpointStatus.CREATING and endpoint_info.endpoint_name not in thread_pool :
            thread = threading.Thread(target=check_deployment_status, args=(endpoint_info.endpoint_name,))
            logger.info(endpoint_info.endpoint_name )
            with endpoints_lock:
                thread_pool[endpoint_info.endpoint_name] = 1
                thread.start()
            
        
    return info,count