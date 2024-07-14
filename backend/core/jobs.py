import time
import uuid
import sys
sys.path.append('../')
import json
import logging
import asyncio
from typing import Annotated, Sequence, TypedDict, Dict, Optional,List, Any,TypedDict

from model.data_model import CommonResponse,CreateJobsRequest, \
ListJobsRequest,JobInfo,JobType,ListJobsResponse,GetJobsRequest, \
JobsResponse,JobStatus,DelJobsRequest,FetchLogRequest,FetchLogResponse,JobStatusResponse
from training.training_job import fetch_log
from db_management.database import DatabaseWrapper
from datetime import datetime
database = DatabaseWrapper()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class APIException(Exception):
    def __init__(self, message, code: str = None):
        if code:
            super().__init__("[{}] {}".format(code, message))
        else:
            super().__init__(message)


async def create_job(request:CreateJobsRequest) -> JobInfo: 
    job_id = str(uuid.uuid4().hex)
    job_name = request.job_name
    job_type = request.job_type
    job_status = JobStatus.SUBMITTED.value
    job_detail = {'job_name': job_name}
    job_create_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    #format job_create_time to '2024-04-29 08:20:03'

    job_start_time = None
    job_end_time = None
    ts = int(time.time())
    job_detail = JobInfo(job_id=job_id,
                        job_name=job_name,
                        job_run_name = '',
                        output_s3_path = '',
                        job_type=job_type,
                        job_status=job_status,
                        job_create_time=job_create_time,
                        job_start_time=job_start_time,
                        job_end_time=job_end_time,
                        job_payload = request.job_payload,
                        ts=ts)
    ret = job_detail if database.save_job(job_detail) else None
    return ret
    
async def get_job_by_id(request:GetJobsRequest) -> JobsResponse:
    results = database.get_job_by_id(request.job_id)
    # print(f"database.get_job_by_id:{results}")
    job_info=None
    if results:
        _,job_id,job_name,job_run_name,output_s3_path,job_type,job_status,job_create_time,job_start_time,job_end_time,job_payload,ts = results[0]
        job_info= JobInfo(job_id=job_id,
                        job_name=job_name,
                        job_run_name=job_run_name,
                        output_s3_path=output_s3_path,
                        job_type=job_type,
                        job_status=job_status,
                        job_create_time=job_create_time,
                        job_start_time=job_start_time,
                        job_end_time=job_end_time,
                        job_payload=json.loads(job_payload),
                        ts=ts)
        print(job_info.json())
    else:
        raise APIException(f"Job {request.job_id} not found")
    return JobsResponse(response_id=str(uuid.uuid4()), body=job_info)


async def delete_job_by_id(request:DelJobsRequest) -> CommonResponse:
    ret = database.delete_job_by_id(request.job_id)
    return CommonResponse(response_id=str(uuid.uuid4()), response={"code":"SUCCESS" if ret else "FAILED","message":"" if ret else "Job already started"})
 
async def list_jobs(request:ListJobsRequest) ->ListJobsResponse: 
    results = database.list_jobs(query_terms=request.query_terms,page_size=request.page_size,page_index=request.page_index)
    count = database.count_jobs(query_terms=request.query_terms)
    # print(f"list_jobs:{results}")
    jobs = [JobInfo(job_id=job_id,
                     job_name=job_name,
                     job_run_name=job_run_name,
                     output_s3_path=output_s3_path,
                        job_type=job_type,
                        job_status=job_status,
                        job_payload=json.loads(job_payload),
                        job_create_time=job_create_time,
                        job_start_time=job_start_time,
                        job_end_time=job_end_time,
                        ts=ts
                    ) 
            for _,job_id,job_name,job_run_name,output_s3_path,job_type,job_status,job_create_time,job_start_time,job_end_time,job_payload,ts in results]
    return ListJobsResponse(response_id= str(uuid.uuid4()), jobs=jobs,total_count=count)



def sync_get_job_by_id(job_id:str) -> JobInfo:
    results = database.get_job_by_id(job_id)
    job_info=None
    if results:
        _,job_id,job_name,job_run_name,output_s3_path,job_type,job_status,job_create_time,job_start_time,job_end_time,job_payload,ts = results[0]
        job_info= JobInfo(job_id=job_id,
                        job_name=job_name,
                        job_run_name=job_run_name,
                        output_s3_path=output_s3_path,
                        job_type=job_type,
                        job_status=job_status,
                        job_create_time=job_create_time,
                        job_start_time=job_start_time,
                        job_end_time=job_end_time,
                        job_payload=json.loads(job_payload),
                        ts=ts)
    else:
        raise Exception(f"Job {job_id} not found")
    return job_info

def update_job_run_name_by_id(job_id:str,job_run_name:str,output_s3_path:str):
    database.update_job_run_name(job_id,job_run_name,output_s3_path)
    
def get_job_status(job_id:str):
    results = database.get_jobs_status_by_id(job_id)
    job_status = None
    if results:
        job_status = results[0][0]
    else:
        raise Exception(f"Job {job_id} not found")
    
    resp = JobStatusResponse(response_id=str(uuid.uuid4()), job_status=JobStatus(job_status))
    return resp
        
    
async def fetch_training_log(request:FetchLogRequest):
    if request.job_run_name :
        logs = fetch_log(log_stream_name=request.job_run_name)
    else:
        logs = ['No logs exists, SageMaker Training Job might not exist']
    return  FetchLogResponse(response_id= str(uuid.uuid4()), log_events=logs)
    
    
if __name__ == '__main__':
    request = CreateJobsRequest(request_id='12231',
        job_type='sft',
        job_name='testmmm',
        job_payload={"model":"llama3","dataset":"ruizhiba"})

    reply = asyncio.run(create_job(request))
    
    request = ListJobsRequest()

    reply = asyncio.run(list_jobs(request))
    print(reply)

