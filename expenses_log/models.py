from django.contrib.auth.models import BaseUserManager
from django.db import models

class ServiceManager(BaseUserManager,models.Manager):
    """
    Common manager for list service functionality that can be used by any model
    with async-only methods
    """
    def get_queryset(self):
        return super().get_queryset().filter(is_valid=True)

    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('username is required')
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(username, password, **extra_fields)