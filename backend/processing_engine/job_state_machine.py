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
JobsResponse,JobStatus
from pydantic import BaseModel,Field
from db_management.database import DatabaseWrapper


logger = logging.getLogger()

logger.setLevel(logging.INFO)
    
    
class JobStateMachine(BaseModel):
    job_status: JobStatus = JobStatus.SUBMITTED
    job_id: str = ""
    handlers : Dict[JobStatus,Any] = None
    database : Any = None
    
    @classmethod
    def create(cls, job_id: str):
        return cls(job_id=job_id,
                   database = DatabaseWrapper(),
                   handlers={
            JobStatus.SUBMITTED: cls.submit_handler,
            JobStatus.RUNNING: cls.run_handler,
            JobStatus.CREATING: cls.creating_handler,
            JobStatus.ERROR: cls.error_handler,
            JobStatus.SUCCESS: cls.success_handler,
            JobStatus.STOPPED: cls.stop_handler,
            JobStatus.PENDING: cls.pending_handler,
            JobStatus.TERMINATED: cls.terminated_handler,
            JobStatus.TERMINATING: cls.terminated_handler            
        })
    
    def submit_handler(self) ->bool:
        print(f"Job {self.job_id} submitted.")
        return True

    def run_handler(self) ->bool:
        print(f"Job {self.job_id} running.")
        return True

    def success_handler(self) ->bool:
        print(f"Job {self.job_id} success.")
        return True
        
    def creating_handler(self) ->bool:
        print(f"Job {self.job_id} creating.")
        return True

    def error_handler(self) ->bool:
        print(f"Job {self.job_id} error.")
        return True

    def stop_handler(self) ->bool:
        print(f"Job {self.job_id} stopped.")
        return True
        
    def pending_handler(self) ->bool:
        print(f"Job {self.job_id} pending.")
        return True
        
    def terminated_handler(self) ->bool:
        print(f"Job {self.job_id} terminated.")
        return True
        
    def terminating_handler(self) ->bool:
        print(f"Job {self.job_id} terminating.")
        return True
        
        
    def transition(self, new_status: JobStatus, rollback=True):
        old_status = self.job_status
        self.job_status = new_status
        #change status in database
        self.database.set_job_status(self.job_id, new_status)
        ret = self.handlers[new_status](self)
        # rollback to previous status
        if not ret and rollback:
            print('rolling back to previous state')
            self.job_status = old_status
            self.database.set_job_status(self.job_id, old_status)
        return ret
        

        
if __name__ == '__main__':
    job = JobStateMachine.create("job-123")
    job.transition(JobStatus.CREATING)
    # job.transition(JobStatus.SUCCESS)
    # job.transition(JobStatus.TERMINATED)