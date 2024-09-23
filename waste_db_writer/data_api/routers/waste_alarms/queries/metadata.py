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
from pydantic import BaseModel

django.setup()
from django.core.exceptions import ObjectDoesNotExist
from database.models import PlantInfo, EdgeBoxInfo, WasteImpurity, WasteDust, WasteHotSpot
from metadata.models import Metadata, MetadataColumn, MetadataLocalization, Filter, FilterItem, FilterItemLocalization, FilterLocalization


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

URL Path: /alarm/metadata/{language}

    The {language} path parameter specifies the language in which the metadata and filter localization should be returned. Example values could be "de" for German or "en" for English.

Parameters:

    language (required): The language code for retrieving metadata and filter localizations.
    metadata_id (optional, default is 1): The ID of the metadata for which data should be retrieved.

Responses:

    Success (HTTP 200):
        Returns a dictionary containing:
            columns: A list of column metadata, including localized title, type, and description.
            filters: A list of filters, including localized filter names, types, descriptions, and filter items.
            primary_key: The primary key of the Metadata object for the given metadata_id.
        Includes a status code "ok" and detailed success message.

    Error Responses (HTTP 404):
        Metadata Not Found: If no metadata is found for the given metadata_id, the response returns an error indicating that the metadata was not found.
        Language Localization Not Found: If no localization exists for the specified language, the response includes an error message specifying that the localization for that language is missing.
        Filter Items Not Found: If active filter items or their localizations for a given filter are missing, an error response is returned with details.

    Error Responses (HTTP 500):
        If an unexpected error occurs, a generic server error with status code 500 is returned, with details about the error.

"""

@router.api_route(
    "/alarm/metadata/{language}", methods=["GET"], tags=["Alarms"], description=description,
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