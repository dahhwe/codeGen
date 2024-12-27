import json
import logging
import uuid

from django.conf import settings
from django.contrib.auth import authenticate, login
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .minio_client import minio_client
from .models import CustomUser, Project
from .permissions import IsAdminUser


class UserProjectsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, email):
        user = get_object_or_404(CustomUser, email=email)
        projects = Project.objects.filter(user=user)
        projects_data = [
            {
                'project_name': project.project_name,
                'description': project.description,
                'project_type': project.project_type,
                'status': project.status,
                'file_name': project.file_name,
                'file_id': project.file_id,
                'created_at': project.created_at,
            }
            for project in projects
        ]
        return Response(projects_data)


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

        project_name = request.data.get('project_name')
        description = request.data.get('description')
        project_type = request.data.get('project_type')
        project_status = request.data.get('status')

        if not project_name or not description or not project_type or not project_status:
            return Response({'error': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)

        project = Project.objects.create(
            user=request.user,
            project_name=project_name,
            description=description,
            project_type=project_type,
            status=project_status,
            file_name=file_name,
            file_id=file_id
        )

        return Response({'file_id': file_id, 'file_name': file_name, 'project_id': project.id})


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
        return Response({'message': 'Информация для а��министратора'})
