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
from database.models import PlantInfo, EdgeBoxInfo, WasteImpurity, WasteSegments, WasteHotSpot, WasteDust

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
    


event_mapping = {
    'impurity': WasteImpurity,
    'dust': WasteDust,
    'hotspot': WasteHotSpot,
}

router = APIRouter(
    route_class=TimedRoute,
)


description = """

    API Description: GET /event
    Purpose:

    This API endpoint retrieves impurity data within a specified date range, optionally filtered by delivery_id and plant_id. The data returned includes impurity details such as the object ID, severity level, timestamp, and associated images.
    Parameters:

        from_date (query parameter, optional): The start date (in UTC) for filtering impurity data. If not provided, the default is the current day.
        to_date (query parameter, optional): The end date (in UTC) for filtering impurity data. If not provided, the default is the day after from_date.
        delivery_id (query parameter, optional): If provided, the API filters impurity data by this delivery_id and returns only records marked as problematic (is_problematic=True).
        plant_id (query parameter, optional): This can be an additional parameter for further filtering by plant, though it is not used in this implementation (it can be added later if necessary).

    Response:

        Success (200):
            Returns a paginated list of impurity records within the specified date range or filtered by delivery_id. Each impurity record contains:
                severity_level: The severity level of the impurity.
                timestamp: The time the impurity record was created.
                image: The URL of the image associated with the impurity.
                image_id: The ID of the associated image.
                delivery_id: The delivery_id associated with the impurity record.
            Includes metadata:
                total_record: The total number of records returned.
                pages: The number of pages available based on the default items_per_page (15).
                items: The current page's records.

        Error Responses:
            404 (Not Found):
                If no matching impurity records are found for the specified filters or date range, a 404 error is returned with a message indicating that no matching query was found.
            500 (Internal Server Error):
                Returned if an unexpected server error occurs during the request, with details provided in the response.

    Examples:

        Success:
            When records matching the from_date, to_date, or delivery_id are found, the API returns a paginated list of impurity data along with metadata like the total records and available pages.
        Failure:
            If no impurity records are found for the given filters or date range, a 404 error is returned.
            If there is an issue with the query or processing, a 500 error will be returned with relevant details.

"""


@router.api_route(
    "/{event}", methods=["GET"], tags=["Impurity"], description=description,
)
def get_impurity_data(response: Response, event:str, from_date:datetime=None, to_date:datetime=None, delivery_id:str=None, plant_id:str=None):
    results = {}
    items_per_page = 15
    try:
        
        if not event in event_mapping:
            results['error'] = {
                "status_code": "bad-request",
                "status_description": f"event {event} not found",
                "detail": f"Failed to map {event} ! event {event} not found"
            }
            response.status_code = status.HTTP_400_BAD_REQUEST
            return results
        
        
        WASTE_EVENT = event_mapping.get(event)
                
        today = datetime.today()

        if from_date is None:
            from_date = datetime(today.year, today.month, today.day)
        
        if to_date is None:
            to_date = from_date + timedelta(days=1)
            
        from_date = from_date.replace(tzinfo=timezone.utc)
        to_date = to_date.replace(tzinfo=timezone.utc) + timedelta(days=1)
        
        if delivery_id is None:
            waste_event = WASTE_EVENT.objects.filter(created_at__range=(from_date, to_date )).order_by('-created_at')
        else:
            waste_event = WASTE_EVENT.objects.filter(delivery_id=delivery_id).order_by('-created_at')
            
        total_record = len(waste_event)
            
        rows = [
            {
                'severity_level': wi.severity_level,
                'timestamp': wi.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'image': wi.img_file,
                'image_id': wi.img_id,
                'delivery_id': wi.delivery_id,
            } for wi in waste_event
        ]
            
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