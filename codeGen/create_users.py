import os

import django

# Set the environment variable for Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'codeGen.settings')

# Setup Django
django.setup()

from django.contrib.auth.models import User


def create_normal_user(username, password):
    user = User.objects.create_user(username=username, password=password)
    user.save()
    print(f'Successfully created normal user: {username}')


def create_admin_user(username, password):
    admin_user = User.objects.create_superuser(username=username, password=password)
    admin_user.save()
    print(f'Successfully created admin user: {username}')


if __name__ == '__main__':
    create_normal_user('user', 'user')
    create_admin_user('admin', 'admin')
