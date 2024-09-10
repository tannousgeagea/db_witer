import uvicorn
from uuid import uuid4
from typing import Optional, Any
from fastapi import FastAPI, Depends, APIRouter
from asgi_correlation_id import CorrelationIdMiddleware
from fastapi.middleware.cors import CORSMiddleware


from fastapi import HTTPException, Body, status, Request
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import http_exception_handler
from asgi_correlation_id import correlation_id

from data_api.routers.waste_impurity import query_impurity
from data_api.routers.waste_dust import query_dust
from data_api.routers.waste_hotspot import query_hotspot
from data_api.routers.waste_alarms import query_alarms
from data_api.routers.waste_segments import query_segments
from data_api.routers.waste_feedback import give_feecback

def create_app() -> FastAPI:
    tags_meta = [
        {
            "name": "Waste Classification DATA API",
            "description": "waste classification data API"
        }
    ]

    app = FastAPI(
        openapi_tags = tags_meta,
        debug=True,
        title="Waste Classification entrypoint API",
        summary="",
        version="0.0.1",
        contact={
            "name": "Tannous Geagea",
            "url": "https://wasteant.com",
            "email": "tannous.geagea@wasteant.com",            
        },
        openapi_url="/openapi.json"
    )

    origins = ["http//localhost:8000"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["*"],
        allow_headers=["X-Requested-With", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )

    app.include_router(query_impurity.router)
    app.include_router(query_segments.router)
    app.include_router(query_dust.router)
    app.include_router(query_hotspot.router)
    app.include_router(query_alarms.router)
    app.include_router(give_feecback.router)
    
    return app

app = create_app()

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status_code": exc.status_code,
            "status_description": exc.detail,
            "detail": exc.detail
        }
    )

@app.exception_handler(Exception)
async def internal_server_error_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "status_code": 500,
            "status_description": "Internal Server Error",
            "detail": "An unexpected error occurred. Please try again later."
        }
    )


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=16055, log_level="debug", reload=True)
