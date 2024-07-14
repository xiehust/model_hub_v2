import argparse
import json
import os
from typing import Generator, Optional, Union, Dict, List, Any
from logger_config import setup_logger
import logging
import dotenv
import fastapi
from fastapi import Depends, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.security.http import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseSettings
from fastapi.security import OAuth2PasswordBearer

import shortuuid
import uvicorn
import time
import uuid
from pydantic import BaseModel,Field
from model.data_model import CommonResponse,CreateJobsRequest \
    ,ListJobsRequest,GetFactoryConfigRequest,GetJobsRequest \
        ,DelJobsRequest,FetchLogRequest,ListS3ObjectsRequest\
            ,S3ObjectsResponse

from core.jobs import create_job,list_jobs,get_job_by_id,delete_job_by_id,fetch_training_log,get_job_status
from core.get_factory_config import get_factory_config
from core.outputs import list_s3_objects

dotenv.load_dotenv()
logger = setup_logger('server.py', log_file='server.log', level=logging.INFO)


class AppSettings(BaseSettings):
    # The address of the model controller.
    api_keys: Optional[List[str]] = None


app_settings = AppSettings(api_keys=os.environ['api_keys'].split(','))
app = fastapi.FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)
headers = {"User-Agent": "Chat Server"}
get_bearer_token = HTTPBearer(auto_error=False)
async def check_api_key(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),
) -> str:
    # print(app_settings.api_keys)
    if app_settings.api_keys:
        if auth is None or (token := auth.credentials) not in app_settings.api_keys:
            raise HTTPException(
                status_code=401,
                detail={
                    "error": {
                        "message": "",
                        "type": "invalid_request_error",
                        "param": None,
                        "code": "invalid_api_key",
                    }
                },
            )
        return token
    else:
        raise HTTPException(
                status_code=403,
                detail={
                    "error": {
                        "message": "",
                        "type": "invalid_request_error",
                        "param": None,
                        "code": "invalid_api_key",
                    }
                },
            )

class ErrorResponse(BaseModel):
    object: str = "error"
    message: str
    code: int


class APIRequestResponse(BaseModel):
    message:str


def create_error_response(code: int, message: str) -> JSONResponse:
    return JSONResponse(
        ErrorResponse(message=message, code=code).json(), status_code=400
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return create_error_response(400, str(exc))

@app.get("/ping")
async def ping():
    return APIRequestResponse(message='ok')

@app.post("/v1/list_jobs",dependencies=[Depends(check_api_key)])
async def handel_list_jobs(request:ListJobsRequest):
    logger.info(request.json())
    resp = await list_jobs(request)
    return resp

@app.post("/v1/get_factory_config",dependencies=[Depends(check_api_key)])
async def get_llama_factory_config(request:GetFactoryConfigRequest):
    resp = await get_factory_config(request)
    return resp

@app.post("/v1/get_job",dependencies=[Depends(check_api_key)])
async def get_job(request:GetJobsRequest):
    resp = await get_job_by_id(request)
    return resp

@app.post("/v1/delete_job",dependencies=[Depends(check_api_key)])
async def delete_job(request:DelJobsRequest):
    resp = await delete_job_by_id(request)
    return resp


@app.post("/v1/create_job",dependencies=[Depends(check_api_key)])
async def handle_create_job(request: CreateJobsRequest):
    request_timestamp = time.time()  
    logger.debug(request.json())
    job_detail = await create_job(request)
    if job_detail:
        body = {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': job_detail
        }
        return CommonResponse(response=body,response_id=str(uuid.uuid4()))
    else:
        body = {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': 'create job failed'
        }
        return CommonResponse(response=body,response_id=str(uuid.uuid4()))
    
@app.post("/v1/fetch_training_log",dependencies=[Depends(check_api_key)])
async def handle_fetch_training_log(request:FetchLogRequest):
    resp = await fetch_training_log(request)
    return resp


@app.post("/v1/get_job_status",dependencies=[Depends(check_api_key)])
async def handle_get_job_status(request:GetJobsRequest):
    resp = get_job_status(request.job_id)
    return resp

@app.post("/v1/list_s3_path",dependencies=[Depends(check_api_key)])
async def handle_list_s3_path(request:ListS3ObjectsRequest):
    ret = list_s3_objects(request.output_s3_path)
    return S3ObjectsResponse(response_id=str(uuid.uuid4()),objects=ret)
    

def create_price_api_server():
    global app_settings
    parser = argparse.ArgumentParser(
        description="Chat RESTful API server."
    )
    parser.add_argument("--host", type=str, default="0.0.0.0", help="host name")
    parser.add_argument("--port", type=int, default=8000, help="port number")
    parser.add_argument(
        "--allow-credentials", action="store_true", help="allow credentials"
    )
    parser.add_argument(
        "--allowed-origins", type=json.loads, default=["*"], help="allowed origins"
    )
    parser.add_argument(
        "--allowed-methods", type=json.loads, default=["*"], help="allowed methods"
    )
    parser.add_argument(
        "--allowed-headers", type=json.loads, default=["*"], help="allowed headers"
    )
    # parser.add_argument(
    #     "--api-keys",
    #     type=lambda s: s.split(","),
    #     help="Optional list of comma separated API keys",
    # )
    parser.add_argument(
        "--ssl",
        action="store_true",
        required=False,
        default=False,
        help="Enable SSL. Requires OS Environment variables 'SSL_KEYFILE' and 'SSL_CERTFILE'.",
    )
    args = parser.parse_args()

    # app.add_middleware(
    #     CORSMiddleware,
    #     allow_origins=args.allowed_origins,
    #     allow_credentials=args.allow_credentials,
    #     allow_methods=args.allowed_methods,
    #     allow_headers=args.allowed_headers,
    # )
    # app_settings.api_keys = args.api_keys

    
    return args

if __name__ == "__main__":
    logger.info('server start')
    args = create_price_api_server()
    logger.info(f"{args}")
    if args.ssl:
        uvicorn.run(
            "server:app",
            host=args.host,
            port=args.port,
            log_level="info",
            ssl_keyfile=os.environ["SSL_KEYFILE"],
            ssl_certfile=os.environ["SSL_CERTFILE"],
        )
    else:
        uvicorn.run("server:app", host=args.host, port=args.port, log_level="info",reload=True,workers=1)
