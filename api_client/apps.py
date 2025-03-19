from django.apps import AppConfig
from .minio_init import init_minio_bucket


class ApiClientConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api_client'

    def ready(self):
        try:
            init_minio_bucket()
        except Exception as e:
            print(f"Failed to initialize MinIO bucket: {e}")
