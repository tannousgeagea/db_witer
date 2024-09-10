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
from database.models import WasteSegments

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

def get_metadata(from_date:datetime, to_date:datetime):
    if isinstance(from_date, str):
        from_date = datetime.strptime(from_date, DATETIME_FORMAT).replace(tzinfo=timezone.utc)

    if isinstance(to_date, str):
        to_date = datetime.strptime(to_date, DATETIME_FORMAT).replace(tzinfo=timezone.utc)
        
    return WasteSegments.objects.filter(timestamp__range=(from_date, to_date)).order_by('timestamp')


if __name__ == "__main__":
    
    detections = get_metadata(
        from_date='2024-07-24 13:35:55',
        to_date='2024-07-24 13:39:23',
    )
    
    
    for d in detections:
        print(d.timestamp)


    