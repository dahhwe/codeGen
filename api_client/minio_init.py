from django.conf import settings
from .minio_client import minio_client

def init_minio_bucket():
    """Инициализация бакета в MinIO"""
    bucket_name = settings.MINIO_BUCKET_NAME
    
    # Проверяем существование бакета
    if not minio_client.bucket_exists(bucket_name):
        # Создаем бакет
        minio_client.make_bucket(bucket_name)
        print(f"Created bucket: {bucket_name}")
    else:
        print(f"Bucket {bucket_name} already exists") 