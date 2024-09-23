
import os
import time
import math
import django
from django.db.models import Q
from fastapi import status
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Callable
from typing import Optional, Dict
from fastapi import Depends
from fastapi import Request
from fastapi import Response
from fastapi import APIRouter
from fastapi import HTTPException
from fastapi.routing import APIRoute
from pydantic import BaseModel

django.setup()
from django.core.exceptions import ObjectDoesNotExist
from database.models import PlantInfo, EdgeBoxInfo, WasteImpurity, WasteDust, WasteHotSpot, WasteFeedback

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
    responses={404: {"description": "Not found"}},
)



description = """

    Insert or Update Feedback

    Description:
    This endpoint allows users to submit feedback for specific waste management events identified by event_uid. Feedback can include comments, ratings, and additional metadata. If feedback already exists for a given event_uid and user_id, it updates the existing feedback; otherwise, it creates a new feedback entry.

    Endpoint:
    POST /feedback/{event_uid}

    Parameters:

        event_uid (path parameter): Unique identifier for the waste management event.
        Request Body (JSON):
            user_id: Identifier of the user submitting the feedback.
            comment (optional): Textual comment regarding the event.
            rating (optional): Numerical rating (e.g., 1-5) given for the event.
            meta_info (optional): Additional metadata related to the feedback.

    Responses:

        200 OK: Feedback successfully inserted or updated.
            Body:

            json

        {
            "event_uid": "{event_uid}",
            "exists": true/false,  // Indicates if the event_uid was found in the system
            "event": "{event_name}",  // Name of the event type if found
            "status_code": "ok",
            "detail": "data retrieved successfully",
            "status_description": "OK"
        }

    404 Not Found: Event identified by event_uid not found.

        Body:

        json

        {
            "error": {
                "status_code": "non-matching-query",
                "status_description": "event_uid was not found",
                "detail": "matching query does not exist. event_uid {event_uid} was not registered for any event"
            }
        }

    500 Internal Server Error: Server encountered an unexpected condition.

        Body:

        json

            {
                "error": {
                    "status_code": "server-error",
                    "status_description": "Internal Server Error",
                    "detail": "{details of the error}"
                }
            }

    Notes:

        This endpoint ensures that feedback data is associated correctly with the respective waste management event and user.
        It handles scenarios where the event UID is not found, ensuring appropriate error responses are provided.
        Feedback can include updates to existing entries or creation of new entries based on the presence of previous feedback from the same user.


    Usage Example:

    bash

    curl -X POST http://0.0.0.0:16055/api/v1/feedback/event_id -H "Content-Type: application/json" -d '{
        "user_id": "user123",
        "comment": "Great initiative!",
        "rating": 5,
        "meta_info": {
            "location": "Area A",
            "temperature": "25°C"
        }
    }'

"""


class Request(BaseModel):
    user_id:Optional[str] = None
    comment:Optional[str] = None
    rating:Optional[int] = None
    meta_info:Optional[Dict] = None
    ack_status:Optional[bool] = None

@router.api_route(
    "/feedback/{event_uid}", methods=["POST"], tags=["Feedback"], description=description,
)
def insert_feedback(response: Response, event_uid:str, request:Request = Depends()):
    results = {}
    try:
        
        e_model = None
        event = 'unknown'
        events_model = [WasteImpurity, WasteDust, WasteHotSpot]
        exists = False
        for event_model in events_model:
            if event_model.objects.filter(event_uid=event_uid).exists():
                exists = True
                event = event_model._meta.model_name
                e_model = event_model.objects.get(event_uid=event_uid)
                continue
        
        if not exists:
            results['error'] = {
                'status_code': "non-matching-query",
                'status_description': f'event_uid was not found',
                'detail': f"matching query does not exist. event_uid {event_uid} was not registered for any event"
            }

            response.status_code = status.HTTP_404_NOT_FOUND
            return results
        
        user_id = request.user_id
        if WasteFeedback.objects.filter(event_uid=event_uid, user_id=user_id).exists():
            waste_feedback = WasteFeedback.objects.get(event_uid=event_uid, user_id=user_id)
            if request.ack_status is not None:
                waste_feedback.ack_status = request.ack_status
            
            if request.comment:
                waste_feedback.comment = request.comment
                
            if request.rating:
                waste_feedback.rating = request.rating
                            
            if request.meta_info:
                waste_feedback.meta_info = request.meta_info
                
        else:
            waste_feedback = WasteFeedback()
            waste_feedback.event_uid = event_uid
            waste_feedback.event = event
            waste_feedback.user_id = user_id
            waste_feedback.ack_status = False
            waste_feedback.rating = 0

            if request.ack_status:
                waste_feedback.ack_status = request.ack_status           

            if waste_feedback.ack_status:
                waste_feedback.rating = e_model.severity_level

            if request.comment:
                waste_feedback.comment = request.comment
                
            if request.rating:
                waste_feedback.rating = request.rating
            
            if request.meta_info:
                waste_feedback.meta_info = request.meta_info
                
        waste_feedback.updated_at = datetime.now(tz=timezone.utc)
        waste_feedback.save()
        
        results = {
            'event_uid': event_uid,
            'exists': exists,
            'event': event,
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