from django.contrib import admin
from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from .views import FileUploadView, FileDownloadView, AdminOnlyView, CreateUserView

urlpatterns = [
    path('create_user/', CreateUserView.as_view(), name='create_user'),

    # path('admin/', admin.site.urls),
    path('upload/', FileUploadView.as_view(), name='file-upload'),
    path('download/<str:file_id>/<str:file_name>/', FileDownloadView.as_view(), name='file-download'),
    path('admin-only/', AdminOnlyView.as_view(), name='admin-only'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='docs'),
]
