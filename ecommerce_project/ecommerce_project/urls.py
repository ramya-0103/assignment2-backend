from django.contrib import admin
from django.urls import path, include
from rest_framework.authtoken import views as auth_views
from django.contrib.auth import views as django_auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # User Authentication
    path('login/', django_auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', django_auth_views.LogoutView.as_view(next_page='/'), name='logout'),

    # Registration - make sure 'store.urls' has your register view
    path('register/', include('store.urls')),  

    # Main app URLs
    path('', include('store.urls')),

    # DRF token authentication endpoint
    path('api/token/', auth_views.obtain_auth_token, name='api_token_auth'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
