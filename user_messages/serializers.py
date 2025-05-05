from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework.validators import UniqueValidator
from .models import Message
from django.utils.timezone import localtime

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    username = serializers.CharField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ('username', 'email', 'password')
    
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user

class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    receiver_username = serializers.CharField(source='receiver.username', read_only=True)
    sent_at = serializers.SerializerMethodField()

    # Obtener la URL de la imagen de la persona que envía/recibe el mensaje
    sender_avatar_url = serializers.SerializerMethodField()
    receiver_avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ['id', 'sender', 'sender_username', 'sender_avatar_url', 'receiver', 'receiver_username', 'receiver_avatar_url', 'content', 'image', 'sent_at']
        read_only_fields = ['sender', 'sent_at']

    def get_sent_at(self, obj):
        local_sent = localtime(obj.sent_at)
        timezone_name = local_sent.tzname() or ''  # Evita None si no tiene zona definida
        return f"{local_sent.strftime('%d/%m/%Y %H:%M:%S')} {timezone_name}"
    
    # Obtener la URL de la imagen de la persona que envía/recibe el mensaje
    def get_sender_avatar_url(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.sender.avatar.url) if obj.sender.avatar else None
    
    def get_receiver_avatar_url(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.receiver.avatar.url) if obj.receiver.avatar else None
    
class UserSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'avatar', 'avatar_url']
        read_only_fields = ['id', 'username', 'email']
    
    def get_avatar_url(self, obj):
        request = self.context.get('request')
        if obj.avatar:
            return request.build_absolute_uri(obj.avatar.url) if request else obj.avatar.url
        return None
    
    def to_representation(self, instance):
        # Fuerza avatar como ruta relativa si hay imagen

        ret = super().to_representation(instance)
        if instance.avatar:
            ret['avatar'] = instance.avatar.url
        return ret