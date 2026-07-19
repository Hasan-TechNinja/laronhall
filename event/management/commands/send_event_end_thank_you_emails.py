from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from event.models import Event
from authentication.emails import send_event_end_thank_you_email

class Command(BaseCommand):
    help = 'Sends thank you emails to event creators when their events end'

    def handle(self, *args, **options):
        now = timezone.now()
        
        # Query events whose end date has passed, and haven't had the thank you email sent yet.
        events = Event.objects.filter(
            end_thank_you_sent=False,
            end_date__lte=now,
            end_date__gte=now - timedelta(days=3)
        )
        
        count = 0
        for event in events:
            if event.creator and event.creator.email:
                organizer_name = event.creator.full_name or event.creator.phone
                
                # Use event name or fall back to Treats Island Candy
                org_name = event.name or "Treats Island Candy"
                
                try:
                    send_event_end_thank_you_email(event.creator.email, organizer_name, org_name)
                    event.end_thank_you_sent = True
                    event.save()
                    count += 1
                    self.stdout.write(self.style.SUCCESS(f"Sent end thank you email to {event.creator.email} for event '{event.name}'"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Failed to send email to {event.creator.email}: {str(e)}"))
                    
        self.stdout.write(self.style.SUCCESS(f"Finished sending end thank you emails. Total emails sent: {count}"))
