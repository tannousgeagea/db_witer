from django.core.management.base import BaseCommand, CommandParser
from django.core.exceptions import FieldError
from django.utils import timezone
from datetime import datetime, timedelta
from database.models import WasteImpurity

class Command(BaseCommand):
    help = "delete instance of WasteImpurity that has been expired"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--days", type=int, default=0, help='how old the data should be in days')
        parser.add_argument("--hours", type=int, default=24, help="how old the data should be in hours")
    
    def handle(self, *args, **kwargs):
        dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            cutoff_time = timezone.now() - timedelta(days=kwargs['days'], hours=kwargs['hours'])
            count, _ = WasteImpurity.objects.filter(timestamp__lt=cutoff_time, is_problematic=False).delete()
            if not count:
                self.stdout.write(self.style.WARNING("No instance has been found"))
                return
            
            dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.stdout.write(self.style.SUCCESS(f"{dt}: Successfully delete {count} old instance."))
        except FieldError as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))
            self.stdout.write(self.style.ERROR(f"{dt}: Make sure you are using the correct field name for filtering."))