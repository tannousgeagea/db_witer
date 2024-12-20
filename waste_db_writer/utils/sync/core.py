import os
from utils.api.base import BaseAPI
from utils.common import DATETIME_FORMAT

base_api = BaseAPI()

def sync_to_alarm(url:str, model, event_name:str, meta_info=None):
    try:
        base_api.post(
            url=url,
            payload={
                'event_id': model.event_uid,
                "source_id": "waste-db-writer",
                "target": "alarm",
                "data": {
                    "tenant_domain": model.edge_box.plant.domain,
                    "delivery_id": str(model.delivery_id) if model.delivery_id else '',
                    "location": model.location if model.location is not None else model.edge_box.edge_box_location,
                    "flag_type": f"{event_name}",
                    "severity_level": str(model.severity_level),
                    "timestamp": model.timestamp.strftime(DATETIME_FORMAT),
                    "event_uid": model.event_uid,
                    "meta_info": meta_info,
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
                        "delivery_id": str(model.delivery_id),
                        "flag_type": "impurity",
                        "severity_level": str(model.severity_level),
                        "event_uid": model.event_uid,
                    }
                }
            )
    except Exception as err:
        raise ValueError(f"Error in sync: {err}")

