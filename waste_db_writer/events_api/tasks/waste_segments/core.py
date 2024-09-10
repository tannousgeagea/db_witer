import os
import django
django.setup()
from celery import shared_task
from datetime import datetime, timezone
from database.models import PlantInfo, EdgeBoxInfo, WasteSegments, WasteImpurity
from utils.common import get_box_info, DATETIME_FORMAT

def save_waste_segments(objects, edge_box):
    success = False
    try:
        assert 'object_uid' in objects.keys(), f'object_uid not Found'
        timestamp = objects.get('timestamp', datetime.now(tz=timezone.utc))
        if isinstance(timestamp, str):
            timestamp = datetime.strptime(timestamp, DATETIME_FORMAT).replace(tzinfo=timezone.utc)
            
        waste_segments = [
            WasteSegments(
                edge_box = edge_box,
                timestamp = timestamp,
                object_uid = objects.get('object_uid')[i],
                object_tracker_id = objects.get('object_tracker_id')[i],
                object_polygon = objects.get('object_polygon')[i],
                confidence_score = objects.get('confidence_score')[i],
                object_area = objects.get('object_area')[i],
                object_length = objects.get('object_length')[i],
                img_id = objects.get('img_id'),
                img_file = objects.get('img_file'),
                model_name = objects.get('model_name'),
                model_tag = objects.get('model_tag'),
                meta_info=objects.get('meta_info'),
                
            ) for i in range(len(objects.get('object_uid', []))) 
            if not WasteSegments.objects.filter(object_uid=objects.get('object_uid')[i]).exists()
        ]

        WasteSegments.objects.bulk_create(waste_segments)
        success = True
    except Exception as err:
        waste_segments = None
        raise ValueError(f"Unexpected error while saving in waste_segments: {err}")
    
    return success, waste_segments

def save_waste_impurity(event, waste_segments):
    success = False
    try:
        timestamp = event.get('timestamp', datetime.now(tz=timezone.utc))
        if isinstance(timestamp, str):
            timestamp = datetime.strptime(timestamp, DATETIME_FORMAT).replace(tzinfo=timezone.utc)
            
        waste_impurity = [
            WasteImpurity(
                edge_box=waste_segment.edge_box,
                timestamp=timestamp,
                object_uid=waste_segment,
                object_tracker_id=waste_segment.object_tracker_id,
                is_long=waste_segment.object_length > 1.,
                is_problematic=False,
                confidence_score=-1,
                severity_level=-1,
                model_name='N/A',
                model_tag='N/A',
            ) for waste_segment in waste_segments
        ]
        
        WasteImpurity.objects.bulk_create(waste_impurity)
        success = True
    except Exception as err:
        raise ValueError(f"Unexpected error while saving in waste_impurity: {err}")

    return success
    
@shared_task(bind=True,autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 5}, ignore_result=True,
             name='waste_segments:save_results_into_database')
def save_results_into_database(self, **kwargs):
    data: dict = {}
    
    info = kwargs
    edge_box = get_box_info()
    suc, waste_segments = save_waste_segments(info, edge_box=edge_box)

    if not suc:
        data.update(
            {
                'action': 'failed',
                'time':  datetime.now().strftime("%Y-%m-%d %H-%M-%S"),
                'result': 'Failed to save waste_segments'
            }
        )
        return data
    
    
    # imp_suc = save_waste_impurity(info, waste_segments=waste_segments)
    data.update(
        {
            'action': 'done',
            'time':  datetime.now().strftime("%Y-%m-%d %H-%M-%S"),
            'result': 'success'
        }
    )
    
    return data
