from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from event.models import Event
from authentication.emails import send_event_twenty_four_hour_reminder_email

class Command(BaseCommand):
    help = 'Sends optimization tips/reminders to event creators 24 hours after their events start'

    def handle(self, *args, **options):
        now = timezone.now()
        twenty_four_hours_ago = now - timedelta(hours=24)
        
        # Query events that started at least 24 hours ago, and haven't had the 24h reminder sent yet.
        events = Event.objects.filter(
            twenty_four_hour_reminder_sent=False,
            start_date__lte=twenty_four_hours_ago,
            start_date__gte=twenty_four_hours_ago - timedelta(days=3)
        )
        
        count = 0
        for event in events:
            if event.creator and event.creator.email:
                organizer_name = ""
                profile = getattr(event.creator, 'profile', None)
                if profile and profile.full_name:
                    organizer_name = profile.full_name
                else:
                    organizer_name = f"{event.creator.first_name} {event.creator.last_name}".strip() or event.creator.phone
                
                try:
                    send_event_twenty_four_hour_reminder_email(event.creator.email, organizer_name)
                    event.twenty_four_hour_reminder_sent = True
                    event.save()
                    count += 1
                    self.stdout.write(self.style.SUCCESS(f"Sent 24h reminder email to {event.creator.email} for event '{event.name}'"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Failed to send email to {event.creator.email}: {str(e)}"))
                    
        self.stdout.write(self.style.SUCCESS(f"Finished sending 24h reminders. Total emails sent: {count}"))
