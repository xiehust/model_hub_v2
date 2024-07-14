import mysql.connector
from mysql.connector import pooling
from typing import Annotated, Sequence, TypedDict, Dict, Optional, List, Any, Literal
import json
import sys
import os
sys.path.append('./')
from pydantic import BaseModel
from model.data_model import JobInfo, JobStatus
MYSQL_CONFIG = {
    'host': os.environ['db_host'],
    'user': os.environ['db_user'],
    'password': os.environ['db_password'],
    'database': os.environ['db_name']
}
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
    connection_pool: Any = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connection_pool = mysql.connector.pooling.MySQLConnectionPool(pool_name="mypool", pool_size=5, **MYSQL_CONFIG)
        
        # Create table
        # with self.connection_pool.get_connection() as connection:
        #     with connection.cursor() as cursor:
        #         cursor.execute(f"""
        #             CREATE TABLE IF NOT EXISTS {JOB_TABLE} (
        #                 id INT AUTO_INCREMENT PRIMARY KEY,
        #                 job_id VARCHAR(255),
        #                 job_name VARCHAR(255),
        #                 job_run_name VARCHAR(255),
        #                 output_s3_path TEXT,
        #                 job_type VARCHAR(50),
        #                 job_status VARCHAR(50),
        #                 job_create_time BIGINT,
        #                 job_start_time BIGINT,
        #                 job_end_time BIGINT,
        #                 job_payload JSON,
        #                 ts BIGINT
        #             )"""
        #         )
        #         connection.commit()

    def save_job(self, job_detail: JobInfo):
        ret = True
        try:
            with self.connection_pool.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        f"INSERT INTO {JOB_TABLE} (job_id, job_name, job_run_name, output_s3_path, job_type, job_status, job_create_time, job_start_time, job_end_time, job_payload, ts) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", 
                        (job_detail.job_id,
                         job_detail.job_name,
                         job_detail.job_run_name,
                         job_detail.output_s3_path,
                         job_detail.job_type.value,
                         job_detail.job_status.value,
                         job_detail.job_create_time,
                         job_detail.job_start_time, 
                         job_detail.job_end_time,
                         json.dumps(job_detail.job_payload, ensure_ascii=False),
                         job_detail.ts)
                    )
                    connection.commit()
        except Exception as e:
            print(f"Error saving job: {e}")
            ret = False
        return ret

    def count_jobs(self, query_terms: Dict[str, Any] = None):
        with self.connection_pool.get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT COUNT(*) FROM {JOB_TABLE}")
                return cursor.fetchone()[0]

    def get_job_by_id(self, id: str):
        with self.connection_pool.get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT * FROM {JOB_TABLE} WHERE job_id = %s", (id,))
                return cursor.fetchall()

    def update_job_run_name(self, job_id: str, job_run_name: str, output_s3_path: str):
        with self.connection_pool.get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(f"UPDATE {JOB_TABLE} SET job_run_name = %s, output_s3_path = %s WHERE job_id = %s", 
                               (job_run_name, output_s3_path, job_id))
                connection.commit()

    def update_job_start_time(self, job_id: str, job_start_time: int):
        with self.connection_pool.get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(f"UPDATE {JOB_TABLE} SET job_start_time = %s WHERE job_id = %s", 
                               (job_start_time, job_id))
                connection.commit()

    def update_job_end_time(self, job_id: str, job_end_time: int):
        with self.connection_pool.get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(f"UPDATE {JOB_TABLE} SET job_end_time = %s WHERE job_id = %s", 
                               (job_end_time, job_id))
                connection.commit()

    def delete_job_by_id(self, id: str) -> bool:
        with self.connection_pool.get_connection() as connection:
            with connection.cursor() as cursor:
                #查询是否存在非SUBMITTED的记录
                # cursor.execute(f"SELECT * FROM {JOB_TABLE} WHERE job_id = %s AND job_status != 'SUBMITTED'", (id,))
                # if cursor.fetchone():
                #     return False
                
                cursor.execute(f"DELETE FROM {JOB_TABLE} WHERE job_id = %s AND ( job_status != 'RUNNING' OR job_status != 'SUCCESS')", (id,))
                connection.commit()
                return True

    def list_jobs(self, query_terms: Dict[str, Any] = None, page_size=20, page_index=1):
        offset = (page_index - 1) * page_size
        with self.connection_pool.get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT * FROM {JOB_TABLE} LIMIT %s OFFSET %s", (page_size, offset))
                return cursor.fetchall()

    def get_jobs_by_status(self, status: JobStatus):
        with self.connection_pool.get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT job_id FROM {JOB_TABLE} WHERE job_status = %s", (status.value,))
                return cursor.fetchall()

    def get_jobs_status_by_id(self, id: str):
        with self.connection_pool.get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT job_status FROM {JOB_TABLE} WHERE job_id = %s", (id,))
                return cursor.fetchall()

    def set_job_status(self, job_id: str, status: JobStatus):
        with self.connection_pool.get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(f"UPDATE {JOB_TABLE} SET job_status = %s WHERE job_id = %s", 
                               (status.value, job_id))
                connection.commit()

    def close(self):
        self.connection_pool.close()
