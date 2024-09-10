from fastapi import HTTPException
from events_api.tasks.waste_segments.core import save_results_into_database as save_segments
from events_api.tasks.waste_impurity.core import save_results_into_database as save_impurity
from events_api.tasks.waste_dust.core import save_results_into_database as save_dust
from events_api.tasks.waste_hotspot.core import save_results_into_database as save_hotspot


TASK_MAPPING = {
        "waste_segments": save_segments,
        "waste_impurity": save_impurity,
        "waste_dust": save_dust,
        "waste_hotspot": save_hotspot,
}


def handle_event(event):   
    return event

    
def task_map(event_type):
    try:
        return TASK_MAPPING[event_type]
    except Exception as err:
        raise HTTPException(status_code=400, detail=f'Failed to map event_type {event_type} to task: {err}')