from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Event, OrganizationType
from .serializers import EventSerializer
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

        if not type_slug or not start_date_str:
            return Response({'error': 'type (slug) and start_date are required'}, status=status.HTTP_400_BAD_REQUEST)

        start_date = parse_datetime(start_date_str)
        if not start_date:
            return Response({'error': 'Invalid start_date format. Use ISO format (e.g., YYYY-MM-DDTHH:MM:SSZ).'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            org_type = OrganizationType.objects.get(slug=type_slug)
        except OrganizationType.DoesNotExist:
            return Response({'error': 'Invalid OrganizationType slug'}, status=status.HTTP_400_BAD_REQUEST)

        end_date = start_date + timedelta(days=5)
        code = generate_unique_code()

        event = Event.objects.create(
            type=org_type,
            start_date=start_date,
            end_date=end_date,
            code=code,
            duration="5"
        )
        event.participants.add(request.user)
        
        serializer = EventSerializer(event)
        return Response({'message': 'Event initialized', 'event': serializer.data}, status=status.HTTP_201_CREATED)

class EventUpdateNameView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, id):
        name = request.data.get('name')
        if not name:
            return Response({'error': 'name is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            event = Event.objects.get(id=id)
        except Event.DoesNotExist:
            return Response({'error': 'Event not found'}, status=status.HTTP_404_NOT_FOUND)

        event.name = name
        event.save()

        serializer = EventSerializer(event)
        return Response({'message': 'Event name updated', 'event': serializer.data}, status=status.HTTP_200_OK)


class EventUpdateEstimatesView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, id):
        estimated_participants = request.data.get('estimated_participants')
        min_estimated_earning = request.data.get('min_estimated_earning')
        max_estimated_earning = request.data.get('max_estimated_earning')

        try:
            event = Event.objects.get(id=id)
        except Event.DoesNotExist:
            return Response({'error': 'Event not found'}, status=status.HTTP_404_NOT_FOUND)

        if estimated_participants is not None:
            event.estimated_participants = estimated_participants
        if min_estimated_earning is not None:
            event.min_estimated_earning = min_estimated_earning
        if max_estimated_earning is not None:
            event.max_estimated_earning = max_estimated_earning

        event.save()

        serializer = EventSerializer(event)
        return Response({'message': 'Event estimates updated', 'event': serializer.data}, status=status.HTTP_200_OK)


class EventDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        try:
            event = Event.objects.get(id=id)
        except Event.DoesNotExist:
            return Response({'error': 'Event not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = EventSerializer(event)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MyEventsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        events = Event.objects.filter(participants=request.user)
        serializer = EventSerializer(events, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OrganizationTypeListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        organization_types = OrganizationType.objects.all()
        # Ensure we have the serializer imported, but we'll import it at the top or here.
        # Actually I should check if it's imported at the top. Wait, let me just return data or use the serializer.
        from .serializers import OrganizationTypeSerializer
        serializer = OrganizationTypeSerializer(organization_types, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
