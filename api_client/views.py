import io
import shutil
import json
import uuid
import zipfile
from pathlib import Path
from zipfile import ZipFile

from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth import get_user_model
from django.http import HttpResponse, StreamingHttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from py_templating_engine.py_templating_engine.environment.templates_environment import TemplatesEnvironment
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .minio_client import minio_client
from .models import CustomUser, Project
from .permissions import IsAdminUser

@extend_schema(
    summary="Авторизация пользователя",
    description="Аутентификация пользователя и получение токена",
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'email': {'type': 'string', 'format': 'email'},
                'password': {'type': 'string', 'format': 'password'},
            },
            'required': ['email', 'password'],
        }
    },
    responses={200: None, 400: None},
)
@method_decorator(csrf_exempt, name='dispatch')
class UserLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        email = request.data.get("email")
        password = request.data.get("password")
        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            Token.objects.filter(user=user).delete()
            token = Token.objects.create(user=user)
            return Response({"message": "Login successful", "token": token.key}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Invalid email or password"}, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    summary="Обработка шаблона",
    description="Генерация кода на основе шаблона и контекста",
    parameters=[
        OpenApiParameter(
            name="project_id",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description="ID проекта для обработки",
            required=True,
        ),
    ],
    request={
        'application/json': {
            'type': 'object',
            'description': 'Контекст для шаблона'
        }
    },
    responses={200: None, 400: None, 404: None, 500: None},
)
@method_decorator(csrf_exempt, name='dispatch')
class ProcessTemplateView(APIView):
    permission_classes = [IsAuthenticated]
    output_dir = None

    def post(self, request):
        project_id = request.query_params.get("project_id")
        if not project_id:
            return JsonResponse({"error": "Project ID is required in query parameters"}, status=400)

        try:
            context_data = request.data
            if not context_data:
                return JsonResponse({"error": "Context data is required in the request body"}, status=400)
        except ValueError as e:
            return JsonResponse({"error": f"Invalid JSON: {str(e)}"}, status=400)

        try:
            project = Project.objects.get(id=project_id)
            file_path = str(project.id)

            template_response = minio_client.get_object(settings.MINIO_BUCKET_NAME, file_path)
            template_data = template_response.read()
            template_response.close()
            template_response.release_conn()

            template_dir = Path("/tmp/template_processing")
            template_dir.mkdir(parents=True, exist_ok=True)
            template_file_path = template_dir / project.file_name

            with open(template_file_path, "wb") as f:
                f.write(template_data)

            archive_name = str(uuid.uuid4())
            archive_extract_dir = template_dir / archive_name
            archive_extract_dir.mkdir(parents=True, exist_ok=True)

            with ZipFile(template_file_path, 'r') as zip_ref:
                zip_ref.extractall(archive_extract_dir)

            context_file_path = archive_extract_dir / "templater.json"
            with open(context_file_path, "wb") as f:
                f.write(json.dumps(context_data).encode())

            templates_env = TemplatesEnvironment(archive_extract_dir)
            self.output_dir = templates_env.render_project()
            return self.stream_zip(self.output_dir)

        except Project.DoesNotExist:
            return JsonResponse({"error": "Project not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    def stream_zip(self, output_dir):
        def zip_generator():
            try:
                with io.BytesIO() as zip_buffer:
                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                        for file in output_dir.rglob("*"):
                            if file.is_file():
                                arcname = file.relative_to(output_dir)
                                zip_file.write(file, arcname=arcname)
                    zip_buffer.seek(0)
                    yield zip_buffer.read()
            finally:
                # Clean up after streaming is complete
                try:
                    shutil.rmtree(output_dir)
                except Exception as e:
                    print(f"Error cleaning up output directory: {e}")

        response = StreamingHttpResponse(zip_generator(), content_type="application/zip")
        response["Content-Disposition"] = 'attachment; filename="processed_template.zip"'
        return response

@extend_schema(
    summary="Получение проектов пользователя",
    description="Получение списка проектов пользователя по email",
    parameters=[
        OpenApiParameter(
            name="email",
            type=OpenApiTypes.EMAIL,
            location=OpenApiParameter.PATH,
            description="Email пользователя",
            required=True,
        ),
    ],
    responses={200: None, 404: None},
)
@method_decorator(csrf_exempt, name='dispatch')
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

@extend_schema(
    summary="Создание пользователя",
    description="Регистрация нового пользователя",
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'email': {'type': 'string', 'format': 'email'},
                'firstname': {'type': 'string'},
                'lastname': {'type': 'string'},
                'password': {'type': 'string', 'format': 'password'},
            },
            'required': ['email', 'firstname', 'lastname', 'password'],
        }
    },
    responses={201: None, 400: None},
)
@method_decorator(csrf_exempt, name='dispatch')
class CreateUserView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        firstname = request.data.get('firstname')
        lastname = request.data.get('lastname')
        password = request.data.get('password')

        if not email or not firstname or not lastname or not password:
            return Response({'error': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)

        user = get_user_model().objects.create_user(email=email, firstname=firstname, lastname=lastname,
                                                    password=password)
        Token.objects.filter(user=user).delete()
        token = Token.objects.create(user=user)

        return Response({'message': 'User created successfully', 'user_id': user.id, 'token': token.key},
                        status=status.HTTP_201_CREATED)

@extend_schema(
    summary="Загрузка шаблона",
    description="Загрузка архива шаблона и создание проекта",
    request={
        'multipart/form-data': {
            'type': 'object',
            'properties': {
                'file': {
                    'type': 'string',
                    'format': 'binary',
                    'description': 'Архив шаблона'
                },
                'json_file': {
                    'type': 'string',
                    'format': 'binary',
                    'description': 'JSON файл для шаблона'
                },
                'project_name': {'type': 'string'},
                'description': {'type': 'string'},
                'project_type': {'type': 'string'},
                'status': {'type': 'string'},
            },
            'required': ['file', 'json_file', 'project_name', 'description', 'project_type', 'status'],
        }
    },
    responses={200: None, 400: None},
)
@method_decorator(csrf_exempt, name='dispatch')
class UploadTemplateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if 'file' not in request.FILES or 'json_file' not in request.FILES:
            return Response({'error': 'Both archive and JSON file must be provided'}, status=status.HTTP_400_BAD_REQUEST)

        file = request.FILES['file']
        json_file = request.FILES['json_file']

        # Проверка, что файл является архивом
        if not zipfile.is_zipfile(file):
            return Response({'error': 'Provided file is not a valid archive'}, status=status.HTTP_400_BAD_REQUEST)

        # Проверка, что JSON файл действительно JSON
        try:
            json_data = json.load(json_file)
        except json.JSONDecodeError:
            return Response({'error': 'Provided file is not a valid JSON'}, status=status.HTTP_400_BAD_REQUEST)

        # Сбрасываем позицию файлов в начало
        file.seek(0)
        json_file.seek(0)

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
            file_name=file.name  # Сохраняем только имя файла
        )

        # Загружаем архив в MinIO
        minio_client.put_object(
            settings.MINIO_BUCKET_NAME,
            str(project.id),  # Используем project_id как имя объекта
            file,
            length=file.size
        )

        # Загружаем JSON в MinIO
        minio_client.put_object(
            settings.MINIO_BUCKET_NAME,
            f"{project.id}_context.json",
            json_file,
            length=json_file.size
        )

        return Response({
            'project_id': project.id,
            'download_url': f'/api_client/download-template/{project.id}/'
        })

@extend_schema(
    summary="Скачивание шаблона",
    description="Скачивание архива шаблона",
    parameters=[
        OpenApiParameter(
            name="project_id",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description="ID проекта",
            required=True,
        ),
    ],
    responses={200: None, 404: None},
)
@method_decorator(csrf_exempt, name='dispatch')
class DownloadTemplateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        try:
            project = Project.objects.get(id=project_id)
            
            response = minio_client.get_object(settings.MINIO_BUCKET_NAME, str(project.id))
            response_data = response.read()
            response.close()
            response.release_conn()

            response = HttpResponse(response_data, content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename="{project.file_name}"'
            return response
            
        except Project.DoesNotExist:
            return Response({"error": "Project not found"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

@extend_schema(
    summary="Административный доступ",
    description="Эндпоинт для проверки административного доступа",
    responses={200: None, 403: None},
)
@method_decorator(csrf_exempt, name='dispatch')
class AdminOnlyView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        return Response({'message': 'Информация для аминистратора'})

@extend_schema(
    summary="Получение списка всех шаблонов",
    description="Возвращает список всех шаблонов, загруженных в систему",
    responses={200: None, 404: None},
)
@method_decorator(csrf_exempt, name='dispatch')
class ListTemplatesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        projects = Project.objects.all()
        templates_data = [
            {
                'project_id': project.id,
                'project_name': project.project_name,
                'description': project.description,
                'project_type': project.project_type,
                'status': project.status,
                'file_name': project.file_name,
                'created_at': project.created_at,
            }
            for project in projects
        ]
        return Response(templates_data)

@extend_schema(
    summary="Получение JSON файла по ID шаблона",
    description="Возвращает JSON файл, загруженный для указанного шаблона",
    parameters=[
        OpenApiParameter(
            name="project_id",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description="ID проекта",
            required=True,
        ),
    ],
    responses={200: None, 404: None},
)
@method_decorator(csrf_exempt, name='dispatch')
class GetTemplateJsonView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        try:
            project = Project.objects.get(id=project_id)
            response = minio_client.get_object(settings.MINIO_BUCKET_NAME, f"{project.id}_context.json")
            json_data = response.read()
            response.close()
            response.release_conn()

            return HttpResponse(json_data, content_type='application/json')
        except Project.DoesNotExist:
            return Response({"error": "Project not found"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)
