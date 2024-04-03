from django.contrib import admin
from .models import User


class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'first_name', 'last_name', 'email', 'is_superuser', 'is_teacher', 'is_student', 'stud_group')
    list_filter = ('is_teacher', 'is_student')
    search_fields = ('username', 'first_name', 'last_name', 'email')


admin.site.register(User, UserAdmin)
