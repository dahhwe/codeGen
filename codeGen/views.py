import json
import logging
import uuid

from django.conf import settings
from django.contrib.auth import authenticate, login
from django.http import HttpResponse
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .minio_client import minio_client
from .models import CustomUser
from .permissions import IsAdminUser


class UserLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return JsonResponse({"message": "Login successful"}, status=status.HTTP_200_OK)
        else:
            return JsonResponse({"error": "Invalid email or password"}, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class CreateUserView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        email = data.get('email')
        firstname = data.get('firstname')
        lastname = data.get('lastname')
        password = data.get('password')

        if not email or not firstname or not lastname or not password:
            return JsonResponse({'error': 'Missing required fields'}, status=400)

        user = CustomUser.objects.create_user(email=email, firstname=firstname, lastname=lastname, password=password)
        return JsonResponse({'message': 'User created successfully', 'user_id': user.id}, status=201)


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
