import argparse
import json
import logging
import os
from typing import Generator, Optional, Union, Dict, List, Any


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
from model.data_model import CommonResponse,CreateJobsRequest,ListJobsRequest,GetFactoryConfigRequest,GetJobsRequest,DelJobsRequest

from core.jobs import create_job,list_jobs,get_job_by_id,delete_job_by_id
from core.get_factory_config import get_factory_config

logger = logging.getLogger(__name__)
logging.basicConfig(filename=__file__, level=logging.INFO,
                    format='[%(asctime)s %(levelname)s] %(message)s',
                    datefmt='%Y-%d-%m %H:%M:%S', encoding="utf-8")

class AppSettings(BaseSettings):
    # The address of the model controller.
    api_keys: Optional[List[str]] = None


app_settings = AppSettings()
app = fastapi.FastAPI()
headers = {"User-Agent": "Chat Server"}
get_bearer_token = HTTPBearer(auto_error=False)
async def check_api_key(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),
) -> str:
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
    print(request.json())
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
    print(request.json())
    job_detail = await create_job(request)
    body = {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': job_detail
    }
    
    return CommonResponse(response=body,response_id=str(uuid.uuid4()))

def create_price_api_server():
    parser = argparse.ArgumentParser(
        description="Chat RESTful API server."
    )
    parser.add_argument("--host", type=str, default="localhost", help="host name")
    parser.add_argument("--port", type=int, default=8001, help="port number")
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
    parser.add_argument(
        "--api-keys",
        type=lambda s: s.split(","),
        help="Optional list of comma separated API keys",
    )
    parser.add_argument(
        "--ssl",
        action="store_true",
        required=False,
        default=False,
        help="Enable SSL. Requires OS Environment variables 'SSL_KEYFILE' and 'SSL_CERTFILE'.",
    )
    args = parser.parse_args()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=args.allowed_origins,
        allow_credentials=args.allow_credentials,
        allow_methods=args.allowed_methods,
        allow_headers=args.allowed_headers,
    )
    app_settings.api_keys = args.api_keys

    logger.info(f"{args}")
    return args

if __name__ == "__main__":
    logger.info('server start')
    args = create_price_api_server()
    if args.ssl:
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            log_level="info",
            ssl_keyfile=os.environ["SSL_KEYFILE"],
            ssl_certfile=os.environ["SSL_CERTFILE"],
        )
    else:
        uvicorn.run(app, host=args.host, port=args.port, log_level="info")