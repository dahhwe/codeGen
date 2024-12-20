import logging
import uuid

from django.conf import settings
from django.http import HttpResponse
from django.middleware.csrf import get_token
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .minio_client import minio_client
from .permissions import IsAdminUser


class FileUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logging.debug(f"Request FILES: {request.FILES}")
        logging.debug(f"Request data: {request.data}")
        logging.debug(f"Request headers: {request.headers}")
        logging.debug(f"CSRF token: {get_token(request)}")

        if 'file' not in request.FILES:
            logging.error("No file provided in the request")
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

        file = request.FILES['file']
        file_id = str(uuid.uuid4())
        file_name = f"{file_id}/{file.name}"

        minio_client.put_object(
            settings.MINIO_BUCKET_NAME,
            file_name,
            file,
            length=file.size
        )

        return Response({'file_id': file_id, 'file_name': file_name})


class FileDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, file_id, file_name):
        file_path = f"{file_id}/{file_name}"
        response = minio_client.get_object(settings.MINIO_BUCKET_NAME, file_path)
        response_data = response.read()
        response.close()
        response.release_conn()

        response = HttpResponse(response_data, content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{file_name}"'
        return response


class AdminOnlyView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        return Response({'message': 'Информация для администратора'})
