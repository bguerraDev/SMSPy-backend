from django.urls import path
from .views import RegisterView, ProtectedView, MessageListCreateView, UserListView, ReceivedMessagesView, SentMessagesView, ProfileView, SendMessageView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'), #login
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'), #renovar token
    path('protected/', ProtectedView.as_view(), name='protected/'), # ver usuario si es autenticado
    path('messages/', MessageListCreateView.as_view(), name='messages'), # ver mensajes del usuario autenticado
    path('users/', UserListView.as_view(), name='user_list'), # lista de usuarios
    path('messages/received/', ReceivedMessagesView.as_view(), name='messages_received'), # mensajes recibidos del usuario (como receptor)
    path('messages/sent/', SentMessagesView.as_view(), name='messages_sent'), # mensajes enviados del usuario (como emisor)
    path('profile/', ProfileView.as_view(), name='profile'), # ver y actualizar avatar del usuario
    path('messages/send/', SendMessageView.as_view(), name='send_message'), # enviar mensaje a otro usuario

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)