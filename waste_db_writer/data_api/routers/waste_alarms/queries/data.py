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

    API Description: GET /alarm
    Purpose:

    This API endpoint retrieves a paginated collection of alarm events within a specified date range and based on applied filters. It allows the user to specify filters, pagination, and date ranges to efficiently query alarm data from the system.
    Parameters:

        filters (query parameter, optional): A string that contains one or more filter conditions, with each filter separated by &. Each filter is in the format filter_name=filter_value, and multiple values can be provided for a single filter, separated by commas (e.g., severity_level=1,2).
        from_date (query parameter, optional): The start date (in UTC) for filtering the alarm events. If not provided, the default is the current day.
        to_date (query parameter, optional): The end date (in UTC) for filtering the alarm events. If not provided, the default is the day after from_date.
        items_per_page (query parameter, optional): The number of alarm items to be displayed per page. Defaults to 15 if not provided.
        page (query parameter, optional): The page number to retrieve. Defaults to 1 if not provided.

    Response:

        Success (200):
            Returns a paginated list of alarms based on the specified filters and date range. Each alarm contains:
                date: The date the alarm was created (formatted as YYYY-MM-DD).
                start: The start time of the alarm (time created).
                end: The time the alarm was closed (if available).
                location: The location metadata, if available.
                event: A description of the event type.
                severity_level: The severity level of the alarm event.
            Includes metadata:
                total_record: The total number of records found.
                filters: The filters applied in the query.
                pages: The total number of pages based on items_per_page.
                items: The alarms returned for the current page.
            Status: "ok" with status description "OK".

        Error Responses:
            400 (Bad Request):
                If items_per_page is set to 0 or a negative value, a 400 error is returned with a message about division by zero.
            404 (Not Found):
                Returned if no matching alarm records are found for the specified filters.
                Error details include status_code: "non-matching-query" or status_code: "not found".
            500 (Internal Server Error):
                Returned if an unexpected server error occurs during the request.
                Error details include status_code: "server-error" and an error description.

    Examples:

        Success:
            When alarms matching the filters are found within the given date range, the API returns a paginated list of alarms with detailed metadata.
        Failure:
            If no alarms are found or there is an issue with the query or filters, a 404 or 400 error will be returned with details.
            
    Components of the Filter:

        Event Filter:
            event=impurity,dust,hotspot
            This means we want to filter for events where the event name is either "impurity", "dust", or "hotspot".

        Severity Level Filter:
            severity_level__gte=2
            This means we want to filter for events where the severity level is greater than or equal to 2.
            Note that severity_level can have different lookup types such as __gte, __lte, __lt, __gt, __contains, and =.
            
        e.g,:
            filters = event=impurity,dust,hotspot&severity_level__gte=2  --> query mentioned events that have severtity_level greater or equal to 2
            filters = event=impurity & severity_level__gt=2  --> query mentioned events that have severtity_level greater to 2
            filters = event=impurity & severity_level=2  --> query mentioned events that have severtity_level exactly equal to 2
            filters = event=all&severity_level__in=1,3  --> query all events that have severtity_level 1 or 3
    
"""


@router.api_route(
    "/alarm", methods=["GET"], tags=["Alarms"], description=descrption
)
def get_alarm(response: Response, filters:str="", from_date:datetime=None, to_date:datetime=None, items_per_page:int=15, page:int=1):
    results = {}
    try:
        today = datetime.today()
        given_filters = {s.split('=')[0]: s.split('=')[1].split(',') for s in filters.split('&') if len(s)}
        
        if from_date is None:
            from_date = datetime(today.year, today.month, today.day)
        
        if to_date is None:
            to_date = from_date + timedelta(days=1)
            
        from_date = from_date.replace(tzinfo=timezone.utc)
        to_date = to_date.replace(tzinfo=timezone.utc) + timedelta(days=1)
        
        
        if page < 1:
            page = 1
        
        if items_per_page<=0:
            results['error'] = {
                'status_code': 400,
                'status_description': f'Bad Request, items_per_pages should not be 0',
                'detail': "division by zero."
            }

            response.status_code = status.HTTP_400_BAD_REQUEST    
            return results
    
        filters = Filter.objects.filter(is_active=True)
        filters = [
            f.filter_name for f in filters
        ]
        
        lookup_filters = Q()
        lookup_filters &= Q(created_at__range=(from_date, to_date ))
        for g_filter in given_filters.keys():
            key = g_filter.split('__')[0]
            if not key in filters:
                continue
            
            if len(given_filters[g_filter])>1:
                lookup_filters &= Q((g_filter, given_filters[g_filter]))
            else:
                lookup_filters &= Q((g_filter, given_filters[g_filter][0]))
                
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
            "pages": math.ceil(total_record / items_per_page),
            "items": data[(page - 1) * items_per_page:page * items_per_page]
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