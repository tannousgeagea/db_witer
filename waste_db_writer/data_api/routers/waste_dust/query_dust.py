import os
import time
import math
import django
from fastapi import status
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Callable
from fastapi import Request
from fastapi import Response
from fastapi import APIRouter
from fastapi import HTTPException
from fastapi.routing import APIRoute
from utils.convertor import poly2xyxy

django.setup()
from django.core.exceptions import ObjectDoesNotExist
from database.models import PlantInfo, EdgeBoxInfo, WasteDust

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
    
router = APIRouter(
    prefix="/api/v1",
    tags=["Dust"],
    route_class=TimedRoute,
    responses={404: {"description": "Not found"}},
)


@router.api_route(
    "/dust/metadata", methods=["GET"], tags=["Dust"]
)
def get_dust_metadata(response: Response, plant_id:str="gml-luh-001"):
    results = {}
    try:
        
        plant_info = PlantInfo.objects.get(plant_id=plant_id)
        plant_meta_info = plant_info.meta_info
        results = {
            'metadata':  {
                'dust': {
                    'plant_id': plant_info.plant_id,
                    'plant_name': plant_info.plant_name,
                    'plant_location': plant_info.plant_location,
                    'service_name': "Staub",
                }
            }
        }
        
        results['status_code'] = "ok"
        results["detail"] = "data retrieved successfully"
        results["status_description"] = "OK"
        
    except ObjectDoesNotExist as e:
        results['error'] = {
            'status_code': "non-matching-query",
            'status_description': f'Matching query was not found',
            'detail': f"matching query does not exist. {e}"
        }

        response.status_code = status.HTTP_404_NOT_FOUND
        
    except HTTPException as e:
        results['error'] = {
            "status_code": "not found",
            "status_description": "Request not Found",
            "detail": f"{e}",
        }
        
        response.status_code = status.HTTP_404_NOT_FOUND
    
    except Exception as e:
        results['error'] = {
            'status_code': 'server-error',
            "status_description": "Internal Server Error",
            "detail": str(e),
        }
        
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    return results

@router.api_route(
    "/dust/data", methods=["GET"], tags=["Dust"]
)
def get_dust_data(response: Response, plant_id:str='gml-luh-001',from_date:datetime=None, to_date:datetime=None):
    results = {}
    items_per_page = 15
    try:
        plant_info = PlantInfo.objects.get(plant_id=plant_id)
        today = datetime.today()

        if from_date is None:
            from_date = datetime(today.year, today.month, today.day)
        
        if to_date is None:
            to_date = from_date + timedelta(days=1)
            
        from_date = from_date.replace(tzinfo=timezone.utc)
        to_date = to_date.replace(tzinfo=timezone.utc) + timedelta(days=1)
        waste_dust = WasteDust.objects.filter(created_at__range=(from_date, to_date )).order_by('-created_at')
        rows = []
        total_record = len(waste_dust)
        
        for wi in waste_dust:
            
            description = wi.meta_info.get('description')
                
            row = {
                'event_uid': wi.event_uid,
                'severity_level': wi.severity_level,
                'timestamp': wi.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'image': wi.img_file,
                'image_id': wi.img_id,
                'description': description,
            }
            
            rows.append(row)
            
        results['data'] = {
            "type": 'collection',
            "total_record": total_record,
            "pages": math.ceil(total_record / items_per_page),
            "items": rows,
        }
        
        results['status_code'] = "ok"
        results["detail"] = "data retrieved successfully"
        results["status_description"] = "OK"
        
    except ObjectDoesNotExist as e:
        results['error'] = {
            'status_code': "non-matching-query",
            'status_description': f'Matching query was not found',
            'detail': f"matching query does not exist. {e}"
        }

        response.status_code = status.HTTP_404_NOT_FOUND
        
    except HTTPException as e:
        results['error'] = {
            "status_code": "not found",
            "status_description": "Request not Found",
            "detail": f"{e}",
        }
        
        response.status_code = status.HTTP_404_NOT_FOUND
    
    except Exception as e:
        results['error'] = {
            'status_code': 'server-error',
            "status_description": "Internal Server Error",
            "detail": str(e),
        }
        
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    return results


@router.api_route(
    "/dust/delivery/{delivery_id}", methods=["GET"], tags=["Dust"]
)
def get_dust_data_by_delivery(response: Response, delivery_id:str):
    results = {}
    
    try:
        waste_dust = WasteDust.objects.filter(delivery_id=delivery_id).order_by('-created_at')
        rows = []
        for wi in waste_dust:
            description = wi.meta_info.get('description')
            row = {
                'object_uid': wi.object_uid.object_uid,
                'severity_level': wi.severity_level,
                'timestamp': wi.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'image': wi.img_file,
                'image_id': wi.img_id,
                'description': description,
            }
            
            rows.append(row)
            
        results['data'] = {
            "type": 'collection',
            "items": rows,
        }
        
        results['status_code'] = "ok"
        results["detail"] = "data retrieved successfully"
        results["status_description"] = "OK"
        
    except ObjectDoesNotExist as e:
        results['error'] = {
            'status_code': "non-matching-query",
            'status_description': f'Matching query was not found',
            'detail': f"matching query does not exist. {e}"
        }

        response.status_code = status.HTTP_404_NOT_FOUND
        
    except HTTPException as e:
        results['error'] = {
            "status_code": "not found",
            "status_description": "Request not Found",
            "detail": f"{e}",
        }
        
        response.status_code = status.HTTP_404_NOT_FOUND
    
    except Exception as e:
        results['error'] = {
            'status_code': 'server-error',
            "status_description": "Internal Server Error",
            "detail": str(e),
        }
        
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    return results

