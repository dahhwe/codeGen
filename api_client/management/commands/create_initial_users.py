from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone

class Command(BaseCommand):
    help = 'Create initial users'

    def handle(self, *args, **kwargs):
        User = get_user_model()

        # Создаем обычного пользователя
        user, created = User.objects.get_or_create(
            username='user',
            defaults={
                'email': 'user@gmail.com',
                'first_name': 'User',
                'last_name': 'User',
                'password': 'user',
                'last_login': timezone.now(),
            }
        )
        if created:
            user.set_password('user')
            user.save()
            self.stdout.write(self.style.SUCCESS('Successfully created user'))

        # Создаем администратора
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@gmail.com',
                'first_name': 'Admin',
                'last_name': 'Admin',
                'password': 'admin',
                'last_login': timezone.now(),
            }
        )
        if created:
            admin_user.set_password('admin')
            admin_user.is_superuser = True
            admin_user.is_staff = True
            admin_user.save()
            self.stdout.write(self.style.SUCCESS('Successfully created admin user')) 