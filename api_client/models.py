from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)

class Project(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    project_name = models.CharField(max_length=255)
    description = models.TextField()
    project_type = models.CharField(max_length=255)
    status = models.CharField(max_length=255)
    file_name = models.CharField(max_length=255)
    file_id = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
