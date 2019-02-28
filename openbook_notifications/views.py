# Create your views here.
from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from openbook_notifications.serializers import GetNotificationsSerializer, GetNotificationsNotificationSerializer, \
    DeleteNotificationSerializer, ReadNotificationSerializer


class Notifications(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        query_params = request.query_params.dict()
        serializer = GetNotificationsSerializer(data=query_params)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        count = data.get('count', 10)
        max_id = data.get('max_id')

        user = request.user

        notifications = user.get_notifications(max_id=max_id)[:count]

        response_serializer = GetNotificationsNotificationSerializer(notifications, many=True,
                                                                     context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)


class ReadAllNotifications(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        user = request.user

        with transaction.atomic():
            user.read_all_notifications()

        return Response(status=status.HTTP_200_OK)


class NotificationItem(APIView):
    permission_classes = (IsAuthenticated,)

    def delete(self, request, notification_id):
        serializer = DeleteNotificationSerializer(data={'notification_id': notification_id})
        serializer.is_valid(raise_exception=True)

        user = request.user

        with transaction.atomic():
            user.delete_notification_with_id(notification_id)

        return Response(status=status.HTTP_200_OK)


class ReadNotification(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, notification_id):
        serializer = ReadNotificationSerializer(data={'notification_id': notification_id})
        serializer.is_valid(raise_exception=True)

        user = request.user

        with transaction.atomic():
            user.read_notification_with_id(notification_id)

        return Response(status=status.HTTP_200_OK)
