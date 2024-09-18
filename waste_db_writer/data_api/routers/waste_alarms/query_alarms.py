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
from utils.convertor import poly2xyxy
from utils.common import event_map, DATETIME_FORMAT

django.setup()
from django.core.exceptions import ObjectDoesNotExist
from database.models import PlantInfo, EdgeBoxInfo, WasteImpurity, WasteDust, WasteHotSpot
from database.models import Metadata, MetadataColumn, MetadataLocalization, Filter, FilterItem, FilterItemLocalization, FilterLocalization

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
    tags=["Alarms"],
    route_class=TimedRoute,
    responses={404: {"description": "Not found"}},
)


@router.api_route(
    "/alarm/metadata/{language}", methods=["GET"], tags=["Alarms"]
)
def get_alarm_metadata(response: Response, language:str="de", metadata_id:int=1):
    results = {}
    try:
        if not MetadataColumn.objects.filter(metadata_id=metadata_id).exists():
            results = {
                "error": {
                    "status_code": "not found",
                    "status_description": f"Metadata ID {metadata_id} not found",
                    "deatil": f"Metadata ID {metadata_id} not found",
                }
            }
            
            response.status_code = status.HTTP_404_NOT_FOUND
            return results

        col = []
        columns = MetadataColumn.objects.filter(metadata_id=metadata_id).select_related('metadata').prefetch_related('localizations')        
        for column in columns:
            localization = column.localizations.filter(language=language).first()
            if not localization:
                results = {
                    "error": {
                        "status_code": "not found",
                        "status_description": f"language {language} not found",
                        "deatil": f"language {language} not found",
                    }
                }
                
                response.status_code = status.HTTP_404_NOT_FOUND
                return results
            
            col.append(
                {
                    column.column_name: {
                        "title": localization.title,
                        "type": column.type,
                        "description": localization.description                        
                    }

                }
            )
            
        _filters = []
        filters = Filter.objects.filter(is_active=True).prefetch_related('localizations')
        for fil in filters:
            localization = fil.localizations.filter(language=language).first()
            if not localization:
                results = {
                    "error": {
                        "status_code": "not found",
                        "status_description": f"language {language} for filter {fil.filter_name} not found",
                        "deatil": f"language {language} for filter {fil.filter_name} not found",
                    }
                }
                
                response.status_code = status.HTTP_404_NOT_FOUND
                return results 
        
            if not FilterItem.objects.filter(filter=fil, is_active=True).exists():
                results = {
                    "error": {
                        "status_code": "not found",
                        "status_description": f" filter items for {fil.filter_name} not found",
                        "deatil": f"filter item for {fil.filter_name} not found",
                    }
                }
                
                response.status_code = status.HTTP_404_NOT_FOUND
                return results 
        
            filter_items = FilterItem.objects.filter(filter=fil, is_active=True).prefetch_related('localizations')
            items = {}
            for fil_item in filter_items:
                filter_item_loc = fil_item.localizations.filter(language=language).first()
                if not filter_item_loc:
                    results = {
                        "error": {
                            "status_code": "not found",
                            "status_description": f"language {language} for filter item {fil_item.item_key} not found",
                            "deatil": f"language {language} for filter item {fil_item.item_key} not found",
                        }
                    }
                    
                    response.status_code = status.HTTP_404_NOT_FOUND
                    return results 

                items[fil_item.item_key] = filter_item_loc.item_value
            
            _filters.append({
                fil.filter_name: {
                    "title": localization.title,
                    "type": fil.type,
                    "description": localization.description,
                    "items": items,
                }
            })
        
        results = {
            "columns": col,
            "filters": _filters,
            "primary_key": Metadata.objects.get(id=metadata_id).primary_key
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


descrption = """
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

        events = 'all'
        severity_filter = {"severity_level__gte": "2"}
        
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
        
        if len(filters):
            filters = filters.replace(" ", "")
            filters = {s.split('=')[0]: s.split('=')[1].split(',') for s in filters.split('&') if len(s)}
            events = filters.get('event', "all")
            severity_filters = {key: value for key, value in filters.items() if key.startswith('severity')}
            severity_filter = severity_filters if severity_filters else severity_filter
            if severity_filter:
                values = severity_filter[list(severity_filter.keys())[0]]
                if len(values) == 1:
                    severity_filter = {key: value[0] for key, value in severity_filter.items()}
        
        data = []
        if 'all' in events:
            events = ['impurity', 'dust', 'hotspot']
            
        for event in events:
            event_mapper = event_map(event_type=event)
            filters = Q()
            filters &= Q(created_at__range=(from_date, to_date ))
            filters &= Q(**severity_filter)
            
            data += event_mapper(filters)
            
        data = sorted(data, key=lambda x: datetime.strptime(f"{x['timestamp']}", DATETIME_FORMAT), reverse=True)
        
        total_record = len(data)
        results['data'] = {
            "type": "collection",
            "total_record": total_record,
            "filters": severity_filter,
            "event": events,
            "pages": math.ceil(total_record / items_per_page),
            "items":data[(page - 1) * items_per_page:page * items_per_page]
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










descrption = """
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
    "/alarm/{event_id}", methods=["GET"], tags=["Alarms"], description=descrption
)
def get_alarm_by_event_id(response: Response, event_id:str):
    results = {}
    try:
        data = []
        events = ['impurity', 'dust', 'hotspot']
        
        for event in events:
            event_mapper = event_map(event_type=event)
            filters = Q()
            filters &= Q(event_uid=event_id)

            data += event_mapper(filters)
            
        data = sorted(data, key=lambda x: datetime.strptime(f"{x['timestamp']}", DATETIME_FORMAT), reverse=True)
        
        total_record = len(data)
        results['data'] = {
            "type": "collection",
            "total_record": total_record,
            "pages": 1,
            "items": data,
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