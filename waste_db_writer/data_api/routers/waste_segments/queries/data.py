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
    route_class=TimedRoute,
)


description = """

    API Description: GET /segments
    Purpose:

    This API endpoint retrieves segment data from the WasteSegments table within a specified date range, optionally filtered by delivery_id. The data includes information about object dimensions, areas, and their polygon coordinates, which are transformed into XY coordinates for convenience.
    Parameters:

        from_date (query parameter, optional): The start date (in UTC) for filtering segment data. Defaults to the current day if not provided.
        to_date (query parameter, optional): The end date (in UTC) for filtering segment data. Defaults to the day after from_date if not provided.
        delivery_id (query parameter, optional): If provided, the API filters segment data by this delivery_id.

    Response:

        Success (200):
            Returns a paginated collection of segment data within the specified date range or filtered by delivery_id. Each segment record contains:
                object_uid: Unique identifier for the segment object.
                timestamp: The timestamp when the segment was created.
                object_length: The length of the segment object.
                object_area: The area of the segment object.
                xyn: The original polygon coordinates of the object.
                xyxyn: The converted XY coordinates of the object (transformed using poly2xyxy).
            Includes metadata:
                total_record: The total number of records returned.
                pages: The number of pages available based on items_per_page (default 15).
                items: The current page's records.

        Error Responses:
            404 (Not Found):
                Returned if no matching segment records are found for the specified filters or date range.
                Error details include status_code: "non-matching-query" or status_code: "not found".
            500 (Internal Server Error):
                Returned if an unexpected server error occurs during the request, with details provided in the response.

    Examples:

        Success:
            When records matching the from_date, to_date, or delivery_id are found, the API returns a paginated list of segment data along with metadata like the total records and available pages.
        Failure:
            If no segment records are found for the given filters or date range, a 404 error is returned.
            If there is an issue with the query or processing, a 500 error will be returned with relevant details.

"""


@router.api_route(
    "/segments", methods=["GET"], tags=["Segments"], description=description,
)
def get_segments_data(response: Response, from_date:datetime=None, to_date:datetime=None, delivery_id:str=None):
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
        
        if delivery_id is None:
            waste_segments = WasteSegments.objects.filter(timestamp__range=(from_date, to_date )).order_by('timestamp')
        else:
            waste_segments = WasteSegments.objects.filter(delivery_id=delivery_id).order_by('timestamp')
            
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