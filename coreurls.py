from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView
from insurance.serializers import CustomTokenObtainPairSerializer
from django.conf import settings
from django.conf.urls.static import static


class CustomLoginView(TokenObtainPairView):
    """Returns access token, refresh token, and detailed user profile with role."""
    serializer_class = CustomTokenObtainPairSerializer


urlpatterns = [
    path('admin/', admin.site.urls),

    # Authentication Endpoints
    path('api/auth/login/', CustomLoginView.as_view(), name='auth_login'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='auth_refresh'),

    # Core Insurance API
    path('api/v1/', include('insurance.urls')),
]
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )