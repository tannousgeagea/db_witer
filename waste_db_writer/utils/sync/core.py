import os
from utils.api.base import BaseAPI
from utils.common import DATETIME_FORMAT

base_api = BaseAPI()

def sync_to_alarm(url:str, model):
    try:
        base_api.post(
            url=url,
            payload={
                'event_id': model.event_uid,
                "source_id": "waste-db-writer",
                "target": "alarm",
                "data": {
                    "tenant_domain": model.edge_box.plant.domain,
                    "delivery_id": model.delivery_id if model.delivery_id else '',
                    "location": model.meta_info.get('region') if model.meta_info is not None else 'bunker',
                    "flag_type": "impurity",
                    "severity_level": str(model.severity_level),
                    "timestamp": model.timestamp.strftime(DATETIME_FORMAT),
                    "event_uid": model.event_uid,
                }
            }
        )
        
        if model.delivery_id:
            base_api.post(
                url=url,
                payload={
                    'event_id': model.event_uid,
                    "source_id": "waste-db-writer",
                    "target": "delivery/flag",
                    "data": {
                        "delivery_id": model.delivery_id,
                        "flag_type": "impurity",
                        "severity_level": str(model.severity_level),
                    }
                }
            )
    except Exception as err:
        raise ValueError(f"Error in sync: {err}")

