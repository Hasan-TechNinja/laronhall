from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from event.models import Event
from authentication.emails import send_event_banking_details_reminder_email

class Command(BaseCommand):
    help = 'Sends banking details reminders to event creators 2 days after campaign starts'

    def handle(self, *args, **options):
        now = timezone.now()
        two_days_ago = now - timedelta(days=2)
        
        # Query events that started at least 2 days ago, and haven't had the banking reminder sent yet.
        events = Event.objects.filter(
            banking_details_reminder_sent=False,
            start_date__lte=two_days_ago,
            start_date__gte=two_days_ago - timedelta(days=3)
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
                    send_event_banking_details_reminder_email(event.creator.email, organizer_name)
                    event.banking_details_reminder_sent = True
                    event.save()
                    count += 1
                    self.stdout.write(self.style.SUCCESS(f"Sent banking details reminder email to {event.creator.email} for event '{event.name}'"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Failed to send email to {event.creator.email}: {str(e)}"))
                    
        self.stdout.write(self.style.SUCCESS(f"Finished sending banking details reminders. Total emails sent: {count}"))
