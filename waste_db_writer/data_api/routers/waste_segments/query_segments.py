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
from utils.common import map_object_to_gate, rois
django.setup()
from django.core.exceptions import ObjectDoesNotExist
from database.models import PlantInfo, EdgeBoxInfo, WasteSegments

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
    tags=["Segments"],
    route_class=TimedRoute,
    responses={404: {"description": "Not found"}},
)


@router.api_route(
    "/segments/metadata", methods=["GET"], tags=["Segments"]
)
def get_impurity_metadata(response: Response, plant_id:str="gml-luh-001"):
    results = {}
    try:
        
        plant_info = PlantInfo.objects.get(plant_id=plant_id)
        plant_meta_info = plant_info.meta_info
        results = {
            'metadata':  {
                'segments': {
                    'service_name': "Segmentation",
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
    "/segments/data", methods=["GET"], tags=["Segments"]
)
def get_segments_data(response: Response, from_date:datetime=None, to_date:datetime=None):
    results = {}
    items_per_page = 15
    try:
        today = datetime.today()

        if from_date is None:
            from_date = datetime(today.year, today.month, today.day)
        
        if to_date is None:
            to_date = from_date + timedelta(days=1)
            
        from_date = from_date.replace(tzinfo=timezone.utc)
        to_date = to_date.replace(tzinfo=timezone.utc)
        waste_segments = WasteSegments.objects.filter(timestamp__range=(from_date, to_date )).order_by('timestamp')
        rows = []
        total_record = len(waste_segments)
        
        for wi in waste_segments:
            xyn = wi.object_polygon
            xyxyn = poly2xyxy(xyn)
            
            row = {
                'object_uid': wi.object_uid,
                'timestamp': wi.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'object_length': wi.object_length,
                'object_area': wi.object_area,
                'xyn': xyn,
                'xyxyn': xyxyn,
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
    "/segments/delivery/{delivery_id}", methods=["GET"], tags=["Segments"]
)
def get_segments_data_by_delivery(response: Response, delivery_id:str):
    results = {}
    
    try:
        waste_segments = WasteSegments.objects.filter(meta_info__delivery_id=delivery_id).order_by('-created_at')
        
        rows = []
        
        for wi in waste_segments:
                
            row = {
                'object_uid': wi.object_uid,
                'timestamp': wi.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'object_length': wi.object_length,
                'object_area': wi.object_area,
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