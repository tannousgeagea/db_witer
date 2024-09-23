import os
import time
import math
import django
from django.db import connection
from django.db.models import Q
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

django.setup()
from django.core.exceptions import ObjectDoesNotExist
from database.models import PlantInfo, EdgeBoxInfo, WasteAlarm
from metadata.models import Filter


DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M:%S"

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

descrption = """
    API Description: GET /alarm/{event_uid}
    Purpose:

    This API endpoint retrieves details of an alarm event by its unique identifier (event_uid). It returns a collection of alarm records associated with the provided event_uid, including metadata about the event, severity level, location, and timestamps.
    Parameters:

        event_uid (path parameter): A unique identifier for the alarm event. The API searches for alarm entries in the WasteAlarm table that match this event_uid.

    Response:

        Success (200):
            Returns a collection of alarm entries that match the provided event_uid. Each alarm contains:
                date: The date the alarm was created (formatted as YYYY-MM-DD).
                start: The time the alarm was created (start time).
                end: The time the alarm was closed (if applicable).
                location: Location of the alarm, if available in the meta_info field.
                event: The event description or type.
                severity_level: The severity level of the alarm.
            Includes metadata:
                total_record: Total number of matching records.
                filters: Filters used in the query (in this case, filtering by event_uid).
                pages: Number of pages (currently hardcoded to 1).
                items: List of alarm event data.
            Status: "ok" with status description "OK".

        Error Responses:
            404 (Not Found):
                Returned if no matching alarm records are found for the given event_uid or if the request fails due to HTTP-related issues.
                Error details include status_code: "non-matching-query" or status_code: "not found".
            500 (Internal Server Error):
                Returned if an unexpected server error occurs while processing the request.
                Error details include status_code: "server-error" and an error description.

    Examples:

        Success:
            When an alarm with the provided event_uid is found, the response contains a list of all matching alarms, their timestamps, severity levels, and other metadata.
        Failure:
            If the event_uid does not exist, a 404 response is returned with an appropriate error message.
    
"""


@router.api_route(
    "/alarm/{event_uid}", methods=["GET"], tags=["Alarms"], description=descrption
)
def get_alarm_by_event_id(response: Response, event_uid:str):
    results = {}
    try:        
        lookup_filters = Q()
        lookup_filters &= Q(event_uid=event_uid)

        waste_alarm = WasteAlarm.objects.filter(lookup_filters).order_by('-created_at')
        data = [
            {
                "date": wa.created_at.strftime(DATE_FORMAT),
                "start": wa.created_at.strftime(TIME_FORMAT),
                "end": wa.created_at.strftime(TIME_FORMAT),
                "location": wa.meta_info.get('location') if wa.meta_info else None,
                "event": wa.event,
                "severity_level": wa.severity_level,
            } for wa in waste_alarm
        ]
        
        total_record = len(waste_alarm)
        results['data'] = {
            "type": "collection",
            "total_record": total_record,
            "filters": lookup_filters,
            "pages": 1,
            "items": data
        }
        
        results['status_code'] = "ok"
        results["detail"] = "data retrieved successfully"
        results["status_description"] = "OK"
        
        connection.close()
        
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