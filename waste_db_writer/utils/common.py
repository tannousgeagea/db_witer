import os
import cv2
import django
import logging
from django.db.models import Q
django.setup()
import numpy as np
from fastapi import HTTPException
from datetime import datetime, timezone,timedelta
from database.models import PlantInfo, EdgeBoxInfo
from database.models import WasteSegments, WasteImpurity, WasteDust, WasteHotSpot
from database.models import WasteFeedback

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
red_square = '🟥'
yellow_square = '🟨'
green_square = '🟩'
orange_square = '🟧'

mapping_flag = {
    0: green_square,
    1: yellow_square,
    2: orange_square,
    3: red_square,
}


def mappig_delivery(delivery_id, region:str=''):
    if str(delivery_id) == 'null':
        delivery_id = 'Keine Zuordnung'
        region = f'[Schätzung {region}]' if region else region
    
    return f'{delivery_id}: {region}' if region else f'{delivery_id}'

def get_box_info(edge_box_id=None):
    if edge_box_id is None:
        edge_box_id = os.environ.get('EDGE_BOX_ID')
    try:
        edge_box = EdgeBoxInfo.objects.get(edge_box_id=edge_box_id)
    except:
        raise HTTPException(status_code=500, detail=f'edge box id not Found {edge_box_id}')
    
    return edge_box


def get_impurity_info(filters):
    data = []
    event_ids = []
    try:
        filters &= Q(is_problematic=True)
        waste_impurity = WasteImpurity.objects.filter(filters).order_by('-created_at')
        for wi in waste_impurity:
            delivery_id = wi.delivery_id
            meta_info = wi.meta_info if wi.meta_info is not None else {}
            delivery_id = mappig_delivery(delivery_id=delivery_id, region=meta_info.get('region'))
            severity_level = mapping_flag[int(wi.severity_level)]
            
            region = "~Bunker"
            if 'region' in meta_info.keys():
                region = meta_info.get('region') if region.lower() == "tor05" else f"~{meta_info.get('region')}"
            
            ack_status = False
            if WasteFeedback.objects.filter(event_uid = wi.event_uid).exists():
                waste_feedback = WasteFeedback.objects.filter(event_uid = wi.event_uid).order_by('-created_at').first()
                ack_status = waste_feedback.ack_status
                severity_level = mapping_flag[int(waste_feedback.rating)]
                
                if not ack_status:
                    continue
            
            if wi.event_uid in event_ids:
                continue
            
            row = {
                'event_uid': wi.event_uid,
                'event':  'impurity',
                'event_name': 'Störstoff',
                'date': (wi.timestamp +  timedelta(hours=2)).strftime('%Y-%m-%d'),
                'start': (wi.timestamp +  timedelta(hours=2)).strftime('%H:%M:%S'),
                'end': (wi.timestamp + timedelta(hours=2)).strftime('%H:%M:%S'),
                'description': meta_info.get('description'),
                'location': region,
                'severity_level': severity_level,
                'image': wi.img_file,
                'image_id': wi.img_id,
                'delivery_id': str(delivery_id),
                'timestamp': wi.timestamp.strftime(DATETIME_FORMAT),
                'has_video': True,
                'ack_status': ack_status,
            }
            
            data.append(row)
            event_ids.append(wi.event_uid)
    except Exception as err:
        raise HTTPException(status_code=500, detail=f'impurity data not Found: {err}')
    
    return data


def get_dust_info(filters):
    data = []
    try:
        waste_dust = WasteDust.objects.filter(filters).order_by('-created_at')
        for wi in waste_dust:
        
            delivery_id = wi.delivery_id
            meta_info = wi.meta_info if wi.meta_info is not None else {}
            delivery_id = mappig_delivery(delivery_id=delivery_id, region=meta_info.get('region'))
            severity_level = mapping_flag[int(wi.severity_level)]
            
            region = "~Bunker"
            if 'region' in meta_info.keys():
                region = meta_info.get('region') if region.lower() == "tor05" else f"~{meta_info.get('region')}"
            
            ack_status = False
            if WasteFeedback.objects.filter(event_uid = wi.event_uid).exists():
                waste_feedback = WasteFeedback.objects.filter(event_uid = wi.event_uid).order_by('-created_at').first()
                ack_status = waste_feedback.ack_status
                severity_level = mapping_flag[int(waste_feedback.rating)]
                
                if not ack_status:
                    continue
                
            row = {
                'event_uid': wi.event_uid,
                'event': 'dust',
                'event_name': 'Staub',
                'date': (wi.timestamp +  timedelta(hours=2)).strftime('%Y-%m-%d'),
                'start': (wi.timestamp +  timedelta(hours=2)).strftime('%H:%M:%S'),
                'end': (wi.timestamp + timedelta(hours=2)).strftime('%H:%M:%S'),
                'description': meta_info.get('description'),
                'location': region,
                'severity_level': severity_level,
                'image': wi.img_file,
                'image_id': wi.img_id,
                'delivery_id': str(delivery_id),
                'timestamp': wi.timestamp.strftime(DATETIME_FORMAT),
                'has_video': False,
                'ack_status': ack_status,
            }
            
            data.append(row)
    except Exception as err:
        raise HTTPException(status_code=500, detail=f'Dust data not Found: {err}')
    
    return data


def get_hotspot_info(filters):
    data = []
    try:
        waste_hotspot = WasteHotSpot.objects.filter(filters).order_by('-created_at')
        for wi in waste_hotspot:
        
            delivery_id = wi.delivery_id
            meta_info = wi.meta_info if wi.meta_info is not None else {}
            delivery_id = mappig_delivery(delivery_id=delivery_id, region=meta_info.get('region'))
            severity_level = mapping_flag[int(wi.severity_level)]
            
            region = "~Bunker"
            if 'region' in meta_info.keys():
                region = meta_info.get('region') if region.lower() == "tor05" else f"~{meta_info.get('region')}"
            ack_status = False
            if WasteFeedback.objects.filter(event_uid = wi.event_uid).exists():
                waste_feedback = WasteFeedback.objects.filter(event_uid = wi.event_uid).order_by('-created_at').first()
                ack_status = waste_feedback.ack_status
                severity_level = mapping_flag[int(waste_feedback.rating)]
                
                if not ack_status:
                    continue
            
            row = {
                'event_uid': wi.event_uid,
                'event': 'hotspot',
                'event_name': 'Hotspot',
                'date': (wi.timestamp +  timedelta(hours=2)).strftime('%Y-%m-%d'),
                'start': (wi.timestamp +  timedelta(hours=2)).strftime('%H:%M:%S'),
                'end': (wi.timestamp + timedelta(hours=2)).strftime('%H:%M:%S'),
                'description': meta_info.get('description'),
                'location': region,
                'severity_level': severity_level,
                'image': wi.img_file,
                'image_id': wi.img_id,
                'delivery_id': str(delivery_id),
                'timestamp': wi.timestamp.strftime(DATETIME_FORMAT),
                'has_video': False,
                'ack_status': ack_status,
            }
            
            data.append(row)
    except Exception as err:
        raise HTTPException(status_code=500, detail=f'Hotspot data not Found: {err}')
    
    return data


EVENT_MAPPING = {
        "impurity": get_impurity_info,
        "dust": get_dust_info,
        "hotspot": get_hotspot_info
}

def event_map(event_type):
    try:
        return EVENT_MAPPING[event_type]
    except Exception as err:
        raise HTTPException(status_code=400, detail=f'Failed to map event_type {event_type} to event: {err}')
    
def rois():
    rois = {
        'Tor06': {'coords': (0.33711753785610205, 0.810818150639534, 0.17714610434087613, 0.20032455643177516, 0.6800097633552488, 0.19869765481269722, 0.5664992772185093, 0.8201740733004742), 'color': (0, 255, 0)},  # Green
    }
     
    return rois   

  

def map_object_to_gate(xyxyn, rois):
    """
    Maps a list or dictionary of bounding box coordinates of detected objects to predefined regions of interest (ROIs) 
    and assigns each object a region and color based on the ROI it falls into.

    Parameters:
    - objects (list or dict): Either a list of normalized bounding box coordinates [x1, y1, x2, y2] or a dictionary with key 'bbxes' containing the list.
    - rois (dict): A dictionary where each key is a region of interest (ROI) name and each value is a dict containing 
            .'coords' (normalized [xmin, ymin, xmax, ymax] of the ROI) 
            . and 'color' (the color to assign to an object in this ROI).

    Returns:
    - dict: The updated dictionary of objects with each object now having 'region' and 'color' keys indicating the ROI name 
            and color it has been assigned based on its bounding box center.

    Raises:
    - AssertionError: If input validation fails for the objects or the ROI coordinates.

    Example usage:
    >>> objects = [{'bbxes': [[0.1, 0.2, 0.3, 0.4]]}]
    >>> rois = {'Zone1': {'coords': [0.0, 0.0, 0.5, 0.5], 'color': (255, 0, 0)}}
    >>> map_objects_to_rois(objects, rois)
    {'bbxes': [[0.1, 0.2, 0.3, 0.4]], 'region': ['Zone1'], 'color': [(255, 0, 0)]}
    """ 
    
    region = 'Bunker'
    fake_size = 1000
    xyxy = np.array([(int(xyxyn[i] * fake_size), int(xyxyn[i + 1] * fake_size)) for i in range(0, len(xyxyn), 2)]).flatten().tolist()
    xmin, ymin, xmax, ymax = xyxy
    center_x, center_y = (xmin + xmax) // 2, (ymax + ymin) // 2
    for roi_name, roi_info in rois.items():
        assert (np.array(roi_info['coords']) <= 1).all(), f'non-normalized or out of bounds coordinate of ROI: {roi_name}'
        
        polygon = [(roi_info['coords'][i], roi_info['coords'][i+1]) for i in range(0, len(roi_info['coords']), 2)]
        
        polygon = [(int(x * fake_size), int(y * fake_size)) for x, y in polygon]
        polygon = np.array(polygon, np.int32)
        polygon = polygon.reshape((-1, 1, 2))
        
        inside = cv2.pointPolygonTest(polygon, (center_x, center_y), True)
        
        if inside>0:
            region = roi_name
            break

    return region

