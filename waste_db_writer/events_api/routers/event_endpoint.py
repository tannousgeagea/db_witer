import json
import time
import uuid
from pathlib import Path
from fastapi import Body
from fastapi import Request
from fastapi import HTTPException
from datetime import datetime
from pydantic import BaseModel
from fastapi.routing import APIRoute
from fastapi import FastAPI, Depends, APIRouter, Request, Header, Response
from typing import Callable, Union, Any, Dict, AnyStr, Optional, List
from typing_extensions import Annotated


import importlib
from events_api.events import handler

class TimedRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            before = time.time()
            response: Response = await original_route_handler(request)
            duration = time.time() - before
            response.headers["X-Response-Time"] = str(duration)
            print(f"route duration: {duration}")
            print(f"route response: {response}")
            print(f"route response headers: {response.headers}")
            return response

        return custom_route_handler


class ApiResponse(BaseModel):
    status: str
    task_id: str
    data: Optional[Dict[AnyStr, Any]] = None


class ApiRequest(BaseModel):
    request: Optional[Dict[AnyStr, Any]] = None


router = APIRouter(
    prefix="/api/v1",
    tags=["EventAPI"],
    route_class=TimedRoute,
    responses={404: {"description": "Not found"}},
)

@router.api_route(
    "/event/{event_type}", methods=["POST"], tags=["EventAPI"]
)
async def handle_event(
    event_type: str,
    payload: ApiRequest = Body(...),
    x_request_id: Annotated[Optional[str], Header()] = None,
) -> ApiResponse:
    
    if not payload.request:
        raise HTTPException(status_code=400, detail="Invalid request payload")
    
    module = handler.task_map(event_type)
    task = module.apply_async(kwargs=payload.request, task_id=x_request_id)
    response_data = {
        "status": "success",
        "task_id": task.id,
        "data": payload.request
    }
    
    return ApiResponse(**response_data)



@router.api_route(
    "/event/{task_id}", methods=["GET"], tags=["EventAPI"], response_model=ApiResponse
)
async def get_event_status(task_id: str, response: Response, x_request_id:Annotated[Optional[str], Header()] = None):
    result = {"status": "received", "task_id": str(uuid.uuid4()), "data": {}}

    return result
