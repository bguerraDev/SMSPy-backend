from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status, generics, permissions
from .serializers import RegisterSerializer, MessageSerializer, User, UserSerializer
from .models import Message
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.conf import settings
from botocore.exceptions import ClientError

import os

class RegisterView(APIView):
    def post(self, request):
        print(request.data)
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response({"message": "Usuario registrado con éxito."}, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProtectedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"message": f"Hola, {request.user.username}. Estás autenticado"})
    
class MessageListCreateView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Devuelve solo los mensajes en los que el usuario está involucrado
        user = self.request.user
        return Message.objects.filter(Q(sender=user) | Q(receiver=user)).order_by('-sent_at')
    
    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)

class UserListView(ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return User.objects.exclude(id=user.id).exclude(username='admin') # TODO ATENCION NOMBRE MODIFICABLE ADMIN

class ReceivedMessagesView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Message.objects.filter(receiver=user).order_by('-sent_at')

class SentMessagesView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Message.objects.filter(sender=user).order_by('-sent_at')

class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        serializer = UserSerializer(request.user, context={'request': request})
        return Response(serializer.data)

    def put(self, request):
        user = request.user

        if 'avatar' in request.FILES and user.avatar:
            try:
                user.avatar.delete(save=False)
            except ClientError as e:
                print(f"Error deleting previous avatar: {e}")

        serializer = UserSerializer(user, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            print(request.FILES)
            print("🔐 AWS_ACCESS_KEY_ID:", os.getenv("AWS_ACCESS_KEY_ID"))
            print("🔐 AWS_SECRET_ACCESS_KEY:", os.getenv("AWS_SECRET_ACCESS_KEY"))
            print("🔐 AWS_STORAGE_BUCKET_NAME:", os.getenv("AWS_STORAGE_BUCKET_NAME"))
            print("💾 DEFAULT_FILE_STORAGE:", settings.DEFAULT_FILE_STORAGE)
            try:
                serializer.save()
                return Response({"message": "Perfil actualizado correctamente", "data": serializer.data})
            except ClientError as e:
                print(f"Error uploading to S3: {e}")
                return Response({"error": f"Failed to upload to S3: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class SendMessageView(generics.CreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)