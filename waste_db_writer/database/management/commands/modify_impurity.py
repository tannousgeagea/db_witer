
import os
from django.core.management.base import BaseCommand, CommandParser
from django.core.exceptions import FieldError
from django.utils import timezone
from datetime import datetime, timedelta
from database.models import WasteImpurity, WasteSegments

class Command(BaseCommand):
    help = "modify instances of WasteImpurity"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--days", type=int, default=0, help='how old the data should be in days')
        parser.add_argument("--hours", type=int, default=24, help="how old the data should be in hours")
    
    def handle(self, *args, **kwargs):
        dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            cutoff_time = timezone.now() - timedelta(days=kwargs['days'], hours=kwargs['hours'])
            waste_impurity = WasteImpurity.objects.all()
            if not len(waste_impurity):
                self.stdout.write(self.style.WARNING("No instance has been found"))
                return
            
            for wi in waste_impurity:
                xi = round(wi.object_uid.object_length * 100)
                if wi.meta_info is not None:
                    wi.meta_info['description'] = f'1 problem. Langteil [{xi}] cm'
                
                else:
                    wi.meta_info = {
                        'description': f'1 problem. Langteil [{xi}] cm'
                    }  
   
                # wi.save()
                self.stdout.write(self.style.SUCCESS(f"{dt}: Successfully modified {wi.event_uid}."))
                
                
            dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.stdout.write(self.style.SUCCESS(f"{dt}: Successfully modified {len(waste_impurity)} old instance."))
        except FieldError as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))
            self.stdout.write(self.style.ERROR(f"{dt}: Make sure you are using the correct field name for filtering."))