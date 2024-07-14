from .sqlite_helper import SQLiteHelper
from typing import Annotated, Sequence, TypedDict, Dict, Optional,List, Any,TypedDict,Literal
import json
import sys
sys.path.append('./')
from pydantic import BaseModel
from model.data_model import JobInfo,JobStatus

SQLITE_DB_PATH="./model_hub.db"
JOB_TABLE = "JOB_TABLE"

def singleton(cls):
    instances = {}

    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance


@singleton
class DatabaseWrapper(BaseModel):
    sqlite_client:SQLiteHelper = SQLiteHelper(db_path=SQLITE_DB_PATH)
    def __init__(self,*args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 创建表
        self.sqlite_client.execute(f"""
            CREATE TABLE IF NOT EXISTS {JOB_TABLE} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT,
                job_name TEXT,
                job_run_name TEXT,
                output_s3_path TEXT,
                job_type TEXT,
                job_status TEXT,
                job_create_time INTEGER,
                job_start_time INTEGER,
                job_end_time INTEGER,
                job_payload TEXT,
                ts INTEGER
            )"""
        )

    def save_job(self,job_detail:JobInfo):
        ret = True
        try:
            self.sqlite_client.execute(
                    f"INSERT INTO {JOB_TABLE} (job_id,job_name, job_run_name, output_s3_path,job_type, job_status, job_create_time, job_start_time, job_end_time, job_payload, ts) VALUES (?,?,?,?, ?, ?, ?, ?,?, ?, ?)", 
                    (job_detail.job_id,
                     job_detail.job_name,
                     job_detail.job_run_name,
                     job_detail.output_s3_path,
                     job_detail.job_type.value,
                     job_detail.job_status.value,
                     job_detail.job_create_time,
                     job_detail.job_start_time, 
                     job_detail.job_end_time,
                     json.dumps(job_detail.job_payload,ensure_ascii=False),
                     job_detail.ts)
            )
        except Exception as e:
            print(f"Error saving job: {e}")
            ret = False
        finally:
            pass
        return ret
    
    def count_jobs(self, query_terms:Dict[str, Any]=None):
        sql = f"SELECT COUNT(*) FROM {JOB_TABLE} WHERE 1=1"
        results = []
        try:
            results = self.sqlite_client.query(sql)
        except Exception as e:
            print(f"Error counting jobs: {e}")
        return results[0][0]
    
    def get_job_by_id(self,id:str):
        sql = f"SELECT * FROM {JOB_TABLE} WHERE job_id='{id}'"
        results = []
        try:
            results = self.sqlite_client.query(sql)
        except Exception as e:
            print(f"Error counting jobs: {e}")
        return results
    
    def update_job_run_name(self,job_id:str,job_run_name:str,output_s3_path:str):
        sql = f"UPDATE {JOB_TABLE} SET job_run_name = ?, output_s3_path = ? WHERE job_id = ?"
        self.sqlite_client.execute(sql, (job_run_name, output_s3_path, job_id))
        
    def update_job_start_time(self,job_id:str,job_start_time:int):
        sql = f"UPDATE {JOB_TABLE} SET job_start_time = {job_start_time} WHERE job_id = '{job_id}'"
        self.sqlite_client.execute(sql)
        
    def update_job_end_time(self,job_id:str,job_end_time:int):
        sql = f"UPDATE {JOB_TABLE} SET job_end_time = {job_end_time} WHERE job_id = '{job_id}'"
        self.sqlite_client.execute(sql)

    
    def delete_job_by_id(self, id:str) ->bool: 
        #查询是否存在非SUBMITTED的记录
        sql = f"SELECT * FROM {JOB_TABLE} WHERE job_id='{id}' and job_status <> 'SUBMITTED'"
        results = self.sqlite_client.query(sql)
        if results:
            return False
        
        sql = f"DELETE FROM {JOB_TABLE} WHERE job_id='{id}' and job_status = 'SUBMITTED' "
        self.sqlite_client.execute(sql)
        return True

    
    def list_jobs(self,query_terms:Dict[str,Any]=None,page_size=20,page_index=1):
        offset = (page_index - 1) * page_size
        sql = f"SELECT * FROM {JOB_TABLE} WHERE 1=1 LIMIT {page_size} OFFSET {offset}"
        results = []
        try:
            results = self.sqlite_client.query(sql)
        except Exception as e:
            print(f"Error listing jobs: {e}")
        finally:
            pass 
        return results

    def get_jobs_by_status(self,status:JobStatus):
        # 查询SUBMITTED状态的job列表
        sql = f"SELECT job_id FROM {JOB_TABLE} WHERE job_status = '{status.value}'"
        results = self.sqlite_client.query(sql)
        return results
    
    def get_jobs_status_by_id(self,id:str):
        sql = f"SELECT job_status FROM {JOB_TABLE} WHERE job_id = '{id}'"
        results = self.sqlite_client.query(sql)
        return results
    
    def set_job_status(self,job_id:str,status:JobStatus):
        sql = f"UPDATE {JOB_TABLE} SET job_status = '{status.value}' WHERE job_id = '{job_id}'"
        self.sqlite_client.execute(sql)
        
    def close(self):
        self.sqlite_client.close()


    
