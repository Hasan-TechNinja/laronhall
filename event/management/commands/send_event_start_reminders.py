from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from event.models import Event
from authentication.emails import send_event_start_soon_email

class Command(BaseCommand):
    help = 'Sends reminder emails to event creators 1 hour before their events start'

    def handle(self, *args, **options):
        now = timezone.now()
        one_hour_from_now = now + timedelta(hours=1)
        
        # Query events that start in the next 1 hour, aren't in the past, and haven't had the reminder sent yet
        events = Event.objects.filter(
            start_reminder_sent=False,
            start_date__lte=one_hour_from_now,
            start_date__gte=now
        )
        
        count = 0
        for event in events:
            if event.creator and event.creator.email:
                organizer_name = event.creator.full_name or event.creator.phone
                
                try:
                    send_event_start_soon_email(event.creator.email, organizer_name)
                    event.start_reminder_sent = True
                    event.save()
                    count += 1
                    self.stdout.write(self.style.SUCCESS(f"Sent reminder email to {event.creator.email} for event '{event.name}'"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Failed to send email to {event.creator.email}: {str(e)}"))
                    
        self.stdout.write(self.style.SUCCESS(f"Finished sending start reminders. Total emails sent: {count}"))
