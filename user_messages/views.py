from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status, generics, permissions
from .serializers import RegisterSerializer, MessageSerializer, User, UserSerializer
from .models import Message
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

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

        # 1. Elimina el avatar anterior si se sube uno nuevo
        if 'avatar' in request.FILES:
            if user.avatar:
                user.avatar.delete(save=False)
            avatar_file = request.FILES['avatar']
            print(user.avatar.url)
            user.avatar.save(avatar_file.name, avatar_file, save=True)

        # 2. Crea un nuevo dict sin el campo 'avatar' para evitar conflictos
        update_data = request.data.copy()
        if 'avatar' in update_data:
            del update_data['avatar']

        # 3. Actualiza otros campos con el serializer
        serializer = UserSerializer(user, data=update_data, partial=True, context={'request': request})
        if serializer.is_valid():
            print(user.avatar.url)
            serializer.save()  # Solo guarda otros campos, no el avatar
            return Response({
                "message": "Perfil actualizado correctamente",
                "data": serializer.data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class SendMessageView(generics.CreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)