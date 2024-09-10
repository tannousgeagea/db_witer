import os
import django
django.setup()
from celery import shared_task
from datetime import datetime, timezone
from database.models import WasteDust
from utils.common import get_box_info, DATETIME_FORMAT

def save_waste_dust(event, edge_box):
    success = False
    try:
        assert 'event_uid' in event.keys(), f'event_uid not Found'
        timestamp = event.get('timestamp', datetime.now(tz=timezone.utc))
        if isinstance(timestamp, str):
            timestamp = datetime.strptime(timestamp, DATETIME_FORMAT).replace(tzinfo=timezone.utc)
            
        waste_dust = WasteDust(
            edge_box = edge_box,
            timestamp = timestamp,
            event_uid = event.get('event_uid'),
            delivery_id = event.get('delivery_id'),
            confidence_score = event.get('confidence_score'),
            severity_level=event.get('severity_level'),
            img_id = event.get('img_id'),
            img_file = event.get('img_file'),
            model_name = event.get('model_name'),
            model_tag = event.get('model_tag'),
            meta_info=event.get('meta_info'),
            )

        waste_dust.save()
        success = True
    except Exception as err:
        waste_dust = None
        raise ValueError(f"Unexpected error while saving in waste_dust: {err}")
    
    return success, waste_dust
    
@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 5}, ignore_result=True,
             name='waste_dust:save_results_into_database')
def save_results_into_database(self, **kwargs):
    data: dict = {}
    
    info = kwargs
    edge_box = get_box_info()
    suc, _ = save_waste_dust(info, edge_box=edge_box)

    if not suc:
        data.update(
            {
                'action': 'failed',
                'time':  datetime.now().strftime("%Y-%m-%d %H-%M-%S"),
                'result': 'Failed to save waste_dust'
            }
        )
        return data
    
    data.update(
        {
            'action': 'done',
            'time':  datetime.now().strftime("%Y-%m-%d %H-%M-%S"),
            'result': 'success'
        }
    )
    
    return data
