from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    is_teacher = models.BooleanField('Преподаватель', default=False)
    is_student = models.BooleanField('Студент', default=False)
    stud_group = models.CharField('Группа', max_length=10, null=True, blank=True)
    profile_photo = models.ImageField('Фото профиля', upload_to='profile_photos/', null=True, blank=True)

    def __str__(self):
        return self.username
