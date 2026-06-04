from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Event, OrganizationType, Fundraiser
from .serializers import EventSerializer, FundraiserSerializer
from django.utils import timezone
from datetime import timedelta
from django.utils.dateparse import parse_datetime
import random
import string

def generate_unique_code():
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if not Event.objects.filter(code=code).exists():
            return code

class EventCreateInitView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        type_slug = request.data.get('type')
        start_date_str = request.data.get('start_date')
        estimated_participants = request.data.get('estimated_participants')
        min_estimated_earning = request.data.get('min_estimated_earning')
        max_estimated_earning = request.data.get('max_estimated_earning')
        team_name = request.data.get('team_name')

        if not type_slug or not start_date_str:
            return Response({'error': 'type (slug) and start_date are required'}, status=status.HTTP_400_BAD_REQUEST)

        active_events = Event.objects.filter(
            participants=request.user,
            end_date__gte=timezone.now()
        )
        if active_events.exists():
            return Response({'error': 'You cannot create a new event while participating in an active one'}, status=status.HTTP_400_BAD_REQUEST)

        start_date = parse_datetime(start_date_str)
        if not start_date:
            return Response({'error': 'Invalid start_date format. Use ISO format (e.g., YYYY-MM-DDTHH:MM:SSZ).'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            org_type = OrganizationType.objects.get(slug=type_slug)
        except OrganizationType.DoesNotExist:
            return Response({'error': 'Invalid OrganizationType slug'}, status=status.HTTP_400_BAD_REQUEST)

        end_date = start_date + timedelta(days=5)
        code = generate_unique_code()
        code = code.upper()

        event = Event.objects.create(
            name=team_name,
            type=org_type,
            start_date=start_date,
            end_date=end_date,
            code=code,
            duration="5",
            creator=request.user,
            estimated_participants=estimated_participants,
            min_estimated_earning=min_estimated_earning,
            max_estimated_earning=max_estimated_earning
        )
        event.participants.add(request.user)
        Fundraiser.objects.get_or_create(user=request.user, event=event)
        
        serializer = EventSerializer(event)
        return Response({'message': 'Event initialized', 'event': serializer.data}, status=status.HTTP_201_CREATED)


class EventUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, id):
        try:
            event = Event.objects.get(id=id)
        except Event.DoesNotExist:
            return Response({'error': 'Event not found'}, status=status.HTTP_404_NOT_FOUND)

        if event.creator != request.user:
            return Response({'error': 'Only the creator can update this event'}, status=status.HTTP_403_FORBIDDEN)

        type_slug = request.data.get('type')
        start_date_str = request.data.get('start_date')
        estimated_participants = request.data.get('estimated_participants')
        min_estimated_earning = request.data.get('min_estimated_earning')
        max_estimated_earning = request.data.get('max_estimated_earning')
        team_name = request.data.get('name')

        if type_slug:
            try:
                org_type = OrganizationType.objects.get(slug=type_slug)
                event.type = org_type
            except OrganizationType.DoesNotExist:
                return Response({'error': 'Invalid OrganizationType slug'}, status=status.HTTP_400_BAD_REQUEST)

        if start_date_str:
            start_date = parse_datetime(start_date_str)
            if not start_date:
                return Response({'error': 'Invalid start_date format.'}, status=status.HTTP_400_BAD_REQUEST)
            event.start_date = start_date
            if event.duration:
                event.end_date = start_date + timedelta(days=int(event.duration))
            
        if estimated_participants is not None:
            event.estimated_participants = estimated_participants
        if min_estimated_earning is not None:
            event.min_estimated_earning = min_estimated_earning
        if max_estimated_earning is not None:
            event.max_estimated_earning = max_estimated_earning
        if team_name is not None:
            event.name = team_name

        event.save()
        serializer = EventSerializer(event)
        return Response({'message': 'Event updated successfully', 'event': serializer.data}, status=status.HTTP_200_OK)


class EventDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        try:
            event = Event.objects.get(id=id)
        except Event.DoesNotExist:
            return Response({'error': 'Event not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = EventSerializer(event)
        return Response(serializer.data, status=status.HTTP_200_OK)


class EventDetailedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        try:
            event = Event.objects.get(id=id)
        except Event.DoesNotExist:
            return Response({'error': 'Event not found'}, status=status.HTTP_404_NOT_FOUND)

        from .serializers import EventDetailedSerializer
        serializer = EventDetailedSerializer(event)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MyEventsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        events = Event.objects.filter(
            participants=request.user,
            end_date__gte=timezone.now()
        ).order_by('-start_date')
        serializer = EventSerializer(events, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MyEventsHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        events = Event.objects.filter(
            participants=request.user,
            end_date__lt=timezone.now()
        ).order_by('-end_date')
        serializer = EventSerializer(events, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OrganizationTypeListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        organization_types = OrganizationType.objects.all()
        # Ensure we have the serializer imported, but we'll import it at the top or here.
        # Actually I should check if it's imported at the top. Wait, let me just return data or use the serializer.
        from .serializers import OrganizationTypeSerializer
        serializer = OrganizationTypeSerializer(organization_types, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class EventJoinView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        code = request.data.get('code').upper()
        if not code:
            return Response({'error': 'Event code is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Case-sensitive code match
        try:
            event = Event.objects.get(code__exact=code)
        except Event.DoesNotExist:
            return Response({'error': 'Invalid event code'}, status=status.HTTP_404_NOT_FOUND)

        if event.end_date and event.end_date < timezone.now():
            return Response({'error': 'Event has already ended'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if user is already participating in an active event
        active_events = Event.objects.filter(
            participants=request.user,
            end_date__gte=timezone.now()
        )
        if active_events.exists() and not active_events.filter(id=event.id).exists():
            return Response({'error': 'You can only join one active event at a time'}, status=status.HTTP_400_BAD_REQUEST)

        event.participants.add(request.user)

        # Create fundraiser record if not exists
        fundraiser, created = Fundraiser.objects.get_or_create(user=request.user, event=event)
        
        serializer = FundraiserSerializer(fundraiser)
        return Response({'message': 'Joined successfully', 'fundraiser': serializer.data}, status=status.HTTP_200_OK)


class FundraiserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        try:
            fundraiser = Fundraiser.objects.get(id=id)
        except Fundraiser.DoesNotExist:
            return Response({'error': 'Fundraiser not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = FundraiserSerializer(fundraiser)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MyFundraiserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, event_id):
        try:
            fundraiser = Fundraiser.objects.get(event_id=event_id, user=request.user)
        except Fundraiser.DoesNotExist:
            return Response({'error': 'Fundraiser not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = FundraiserSerializer(fundraiser)
        return Response(serializer.data, status=status.HTTP_200_OK)

class FundraiserUpdateNameView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, id):
        name = request.data.get('name')
        if not name:
            return Response({'error': 'Name is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            fundraiser = Fundraiser.objects.get(id=id, user=request.user)
        except Fundraiser.DoesNotExist:
            return Response({'error': 'Fundraiser not found'}, status=status.HTTP_404_NOT_FOUND)

        fundraiser.name = name
        fundraiser.save()
        serializer = FundraiserSerializer(fundraiser)
        return Response({'message': 'Name updated', 'fundraiser': serializer.data}, status=status.HTTP_200_OK)


class FundraiserUpdateGoalView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, id):
        goal = request.data.get('goal')
        if goal is None:
            return Response({'error': 'Goal is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            fundraiser = Fundraiser.objects.get(id=id, user=request.user)
        except Fundraiser.DoesNotExist:
            return Response({'error': 'Fundraiser not found'}, status=status.HTTP_404_NOT_FOUND)

        fundraiser.goal = goal
        fundraiser.save()
        serializer = FundraiserSerializer(fundraiser)
        return Response({'message': 'Goal updated', 'fundraiser': serializer.data}, status=status.HTTP_200_OK)


class FundraiserUpdateDescriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, id):
        description = request.data.get('description')
        if not description:
            return Response({'error': 'Description is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            fundraiser = Fundraiser.objects.get(id=id, user=request.user)
        except Fundraiser.DoesNotExist:
            return Response({'error': 'Fundraiser not found'}, status=status.HTTP_404_NOT_FOUND)

        fundraiser.description = description
        fundraiser.save()
        serializer = FundraiserSerializer(fundraiser)
        return Response({'message': 'Description updated', 'fundraiser': serializer.data}, status=status.HTTP_200_OK)


class FundraiserUpdateMediaView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, id):
        try:
            fundraiser = Fundraiser.objects.get(id=id, user=request.user)
        except Fundraiser.DoesNotExist:
            return Response({'error': 'Fundraiser not found'}, status=status.HTTP_404_NOT_FOUND)

        if 'image' not in request.FILES and 'image' not in request.data and 'video' not in request.FILES and 'video' not in request.data:
            return Response({'error': 'Please provide either an image or a video.'}, status=status.HTTP_400_BAD_REQUEST)

        if 'image' in request.FILES:
            fundraiser.image = request.FILES['image']
        elif 'image' in request.data:
            fundraiser.image = request.data['image']
            
        if 'video' in request.FILES:
            fundraiser.video = request.FILES['video']
        elif 'video' in request.data:
            fundraiser.video = request.data['video']

        fundraiser.save()
        serializer = FundraiserSerializer(fundraiser)
        return Response({'message': 'Media updated', 'fundraiser': serializer.data}, status=status.HTTP_200_OK)


class EventExtendView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        try:
            event = Event.objects.get(id=id)
        except Event.DoesNotExist:
            return Response({'error': 'Event not found'}, status=status.HTTP_404_NOT_FOUND)

        if event.creator != request.user:
            return Response({'error': 'Only the creator can extend this event'}, status=status.HTTP_403_FORBIDDEN)

        if event.duration == "7":
            return Response({'error': 'Event has already been extended to the maximum 7 days'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Extend the event
        if event.end_date:
            event.end_date = event.end_date + timedelta(days=2)
        else:
            event.end_date = event.start_date + timedelta(days=7)
            
        event.duration = "7"
        event.save()
        
        serializer = EventSerializer(event)
        return Response({'message': 'Event extended successfully', 'event': serializer.data}, status=status.HTTP_200_OK)


class EventFundraiserListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, event_id):
        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return Response({'error': 'Event not found'}, status=status.HTTP_404_NOT_FOUND)

        fundraisers = Fundraiser.objects.filter(event=event)
        serializer = FundraiserSerializer(fundraisers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class EventDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, id):
        try:
            event = Event.objects.get(id=id)
        except Event.DoesNotExist:
            return Response({'error': 'Event not found'}, status=status.HTTP_404_NOT_FOUND)

        if event.creator != request.user:
            return Response({'error': 'Only the creator can delete this event'}, status=status.HTTP_403_FORBIDDEN)

        if event.end_date and event.end_date >= timezone.now():
            return Response({'error': 'Cannot delete an active event before its end time is over'}, status=status.HTTP_400_BAD_REQUEST)

        event.delete()
        return Response({'message': 'Event deleted successfully'}, status=status.HTTP_200_OK)

class EventLeaderboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, event_id):
        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            return Response({'error': 'Event not found'}, status=status.HTTP_404_NOT_FOUND)

        fundraisers = Fundraiser.objects.filter(event=event)
        serializer = FundraiserSerializer(fundraisers, many=True)
        
        # Sort the data by the 'achieved' amount in descending order
        sorted_data = sorted(serializer.data, key=lambda x: x.get('achieved', 0), reverse=True)
        
        # Add rank based on position
        for index, item in enumerate(sorted_data):
            item['rank'] = index + 1

        return Response(sorted_data, status=status.HTTP_200_OK)

class FundraiserSupporterListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, id):
        try:
            fundraiser = Fundraiser.objects.get(id=id)
        except Fundraiser.DoesNotExist:
            return Response({'error': 'Fundraiser not found'}, status=status.HTTP_404_NOT_FOUND)

        from shop.models import Order
        from django.db.models.functions import Coalesce, Cast
        from django.db.models import Sum, Count, F, FloatField

        orders = Order.objects.filter(fundraiser=fundraiser, is_paid=True).annotate(
            supporter_email=Coalesce('user__email', 'email'),
            supporter_name=Coalesce('user__profile__full_name', 'name')
        ).values(
            'supporter_email',
            'supporter_name',
            'user__profile__image'
        ).annotate(
            total_orders=Count('id'),
            total_amount=Sum(
                Cast(F('product__price'), FloatField()) * F('quantity'),
                output_field=FloatField()
            )
        ).order_by('-total_amount')

        supporters = []
        for order in orders:
            image_url = None
            if order.get('user__profile__image'):
                image_url = request.build_absolute_uri('/media/' + order.get('user__profile__image'))
            
            supporters.append({
                'name': order.get('supporter_name'),
                'email': order.get('supporter_email'),
                'image': image_url,
                'total_purchased_amount': order.get('total_amount', 0),
                'total_orders': order.get('total_orders', 0)
            })

        return Response(supporters, status=status.HTTP_200_OK)
