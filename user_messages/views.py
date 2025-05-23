from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status, generics, permissions
from .serializers import RegisterSerializer, MessageSerializer, User, UserSerializer
from .models import Message
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
import boto3
from django.conf import settings
from urllib.parse import quote_plus


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
        # TODO ATENCION NOMBRE MODIFICABLE ADMIN
        return User.objects.exclude(id=user.id).exclude(username='admin')


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
        avatar_file = request.FILES.get("avatar")

        if avatar_file:
            # Subida a S3
            s3 = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME
            )
            if user.avatar and user.avatar.name:
                try:
                    s3.delete_object(
                        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                        Key=user.avatar.name
                    )
                except Exception as e:
                    print(f"⚠️ Error al borrar el avatar anterior: {e}")
            # Construye nombre único: username_nombrearchivo.png
            safe_username = quote_plus(user.username)
            safe_filename = quote_plus(avatar_file.name)
            s3_key = f"avatars/{safe_username}_{safe_filename}"
            s3.upload_fileobj(
                avatar_file.file,
                settings.AWS_STORAGE_BUCKET_NAME,
                s3_key,
                ExtraArgs={
                    "ContentType": avatar_file.content_type,
                    "ContentDisposition": "inline",
                }
            )
            # Asigna nombre manualmente al avatar en el modelo
            print(">>> Avatar file name:", avatar_file.name)
            user.avatar.name = s3_key
            user.save()
        serializer = UserSerializer(user, context={'request': request})
        return Response({
            "message": "Perfil actualizado correctamente",
            "data": serializer.data
        })


class SendMessageView(generics.CreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)
