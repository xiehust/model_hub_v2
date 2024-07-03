import time
import uuid
import sys
sys.path.append('./')
import json
import logging
import asyncio
from typing import Annotated, Sequence, TypedDict, Dict, Optional,List, Any,TypedDict

from model.data_model import CommonResponse,CreateJobsRequest, \
ListJobsRequest,JobInfo,JobType,ListJobsResponse,GetJobsRequest, \
JobsResponse,JobStatus,DelJobsRequest
from job_state_machine import JobStateMachine

from db_management.database import DatabaseWrapper
import threading

database = DatabaseWrapper()

def get_submitted_jobs():
    results = database.get_jobs_by_status(JobStatus.SUBMITTED)
    return [ret[0] for ret in results]

def proccessing_job(job_id:str):
    print("start process job:", job_id)
    job = JobStateMachine.create(job_id)
    job.transition(JobStatus.CREATING)
    job.transition(JobStatus.RUNNING)
    print("finish process job:", job_id)
    return True

if __name__ == '__main__':
    processing_threads = {}
    while True:
        results = get_submitted_jobs()
        print("scan job list:",results)
        if results:
            for job_id in results:
                if job_id not in processing_threads:
                    thread = threading.Thread(target=proccessing_job,args=(job_id,))
                    thread.start()
                    processing_threads[job_id]=thread
        
        time.sleep(10)# 每10s扫描一次

        
