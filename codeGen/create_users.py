import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'codeGen.settings')
django.setup()

from .models import CustomUser

def create_normal_user(username, password):
    user = CustomUser.objects.create_user(
        password=password,
        email='user@gmail.com',
        firstname='name',
        lastname='name',
    )
    user.save()
    print(f'Successfully created normal user: {username}')


def create_admin_user(username, password):
    admin_user = CustomUser.objects.create_user(
        password=password,
        email='admin@gmail.com',
        firstname='name',
        lastname='name',
    )
    admin_user.save()
    print(f'Successfully created admin user: {username}')


if __name__ == '__main__':
    create_normal_user('user', 'user')
    create_admin_user('admin', 'admin')
