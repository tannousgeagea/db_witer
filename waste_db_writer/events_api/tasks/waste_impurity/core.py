import django
django.setup()
from celery import shared_task
from datetime import datetime, timezone
from database.models import PlantInfo, EdgeBoxInfo, WasteSegments, WasteImpurity
from utils.common import get_box_info, DATETIME_FORMAT


def update_waste_impurity(objects, edge_box):
    success = False
    try:
        assert 'object_uid' in objects.keys(), f'object_uid not Found'
        timestamp = objects.get('timestamp', datetime.now(tz=timezone.utc))
        if isinstance(timestamp, str):
            timestamp = datetime.strptime(timestamp, DATETIME_FORMAT).replace(tzinfo=timezone.utc)
        
        for i in range(len(objects.get('object_uid', []))):
            waste_segment = WasteSegments.objects.get(object_uid=objects.get('object_uid')[i], edge_box=edge_box)
            
            waste_impurity = WasteImpurity()
            waste_impurity.edge_box = edge_box
            waste_impurity.timestamp = timestamp
            waste_impurity.object_uid = waste_segment
            waste_impurity.event_uid = objects.get('event_uid')
            waste_impurity.delivery_id =  objects.get('delivery_id') 
            waste_impurity.is_problematic = True
            waste_impurity.is_long = True
            waste_impurity.object_tracker_id = waste_segment.object_tracker_id
            waste_impurity.model_name = objects.get('model_name')
            waste_impurity.model_tag = objects.get('model_tag')
            waste_impurity.confidence_score = objects.get('confidence_score')[i]
            waste_impurity.severity_level = objects.get('severity_level')[i]
            waste_impurity.img_id = objects.get('img_id')
            waste_impurity.img_file = objects.get('img_file')
            waste_impurity.meta_info = objects.get('meta_info')
            waste_impurity.save()
            
            waste_segment.img_id = objects.get('img_id')
            waste_segment.img_file = objects.get('img_file')
            waste_segment.save()
        
        success = True
    except Exception as err:
        raise ValueError(f"Unexpected error while saving in waste_impurity: {err}")

    return success


@shared_task(bind=True,autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 5}, ignore_result=True,
             name='waste_impurity:save_impurity_into_database')
def save_results_into_database(self, **kwargs):
    data: dict = {}
    
    info = kwargs
    edge_box = get_box_info(edge_box_id=info.get('EDGE_BOX_ID'))
    suc = update_waste_impurity(objects=info, edge_box=edge_box)
    
    if not suc:
        data.update(
            {
                'action': 'failed',
                'time':  datetime.now().strftime("%Y-%m-%d %H-%M-%S"),
                'result': 'Failed to update waste_impurity'
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