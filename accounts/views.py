import os
import random
import string
from django.conf import settings
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.db.models import Max
from django.http import HttpResponseServerError
from django.shortcuts import render, redirect
from django.utils import timezone
from django.utils.text import slugify
from transliterate import translit
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from datetime import datetime
from tests.models import Subject, Test, TestAttempt, TestActivationSettings
from .forms import ProfilePhotoForm, ChangePasswordForm
from .models import User


@user_passes_test(lambda u: u.is_superuser, login_url='login_view')
def upload_teachers(request):
    if request.method == 'POST':
        if 'file' in request.FILES:  # Проверяем, был ли загружен файл
            file = request.FILES['file']
            lines = file.read().decode('cp1251').splitlines()

            # Определяем путь к директории, где хотим сохранить файл
            file_path = os.path.join(settings.BASE_DIR, 'accounts', f'teachers.txt')

            # Открываем файл для записи
            try:
                with open(file_path, 'w') as f:
                    for line in lines:
                        last_name, first_name, patronymic = line.strip().split(' ')
                        username = slugify(translit(last_name + first_name[0] + patronymic[0], 'ru', reversed=True))
                        password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

                        # Записываем имя пользователя и пароль в файл
                        f.write(f'{last_name} {first_name} {patronymic} - login: {username}, password: {password}\n')

                        # Создаем пользователя и преподавателя
                        user = User.objects.create(username=username, password=make_password(password), last_name=last_name,
                                                   first_name=first_name, is_teacher=True)

                return redirect('accounts:upload_teachers')
            except Exception as e:
                return HttpResponseServerError()
        else:
            # Если файл не был загружен, обрабатываем добавление пользователя вручную
            last_name = request.POST.get('last_name')
            first_name = request.POST.get('first_name')
            patronymic = request.POST.get('patronymic')

            username = slugify(translit(last_name + first_name[0] + patronymic[0], 'ru', reversed=True))
            password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

            try:
                # Создаем преподавателя
                user = User.objects.create(username=username, password=make_password(password), last_name=last_name,
                                           first_name=first_name, is_teacher=True)

                # Записываем информацию о пользователе в файл
                file_path = os.path.join(settings.BASE_DIR, 'accounts', f'teachers.txt')
                with open(file_path, 'a') as f:
                    f.write(f'{last_name} {first_name} {patronymic} - login: {username}, password: {password}\n')

                return redirect('accounts:upload_teachers')
            except Exception as e:
                return HttpResponseServerError()
    else:
        return render(request, 'accounts/upload_teachers.html')


@user_passes_test(lambda u: u.is_superuser, login_url='login_view')
def upload_students(request):
    if request.method == 'POST':
        upload_type = request.POST.get('upload_type')
        group_number = request.POST.get('group_number')
        group = group_number

        if upload_type == 'file':
            file = request.FILES['file']
            lines = file.read().decode('cp1251').splitlines()

            # Определяем путь к директории, где хотим сохранить файл
            file_path = os.path.join(settings.BASE_DIR, 'accounts', f'{group_number}.txt')

            # Открываем файл для записи
            try:
                with open(file_path, 'w') as f:
                    for line in lines:
                        last_name, first_name, patronymic = line.strip().split(' ')
                        username = slugify(translit(last_name + first_name[0] + patronymic[0], 'ru', reversed=True))
                        password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

                        # Записываем имя пользователя и пароль в файл
                        f.write(f'{last_name} {first_name} {patronymic} - login: {username}, password: {password}\n')

                        # Создаем пользователя и студента
                        user = User.objects.create(username=username, password=make_password(password), last_name=last_name,
                                                   first_name=first_name, stud_group=group, is_student=True)
                return redirect('accounts:upload_students')
            except Exception as e:
                return redirect('accounts:upload_students')
        elif upload_type == 'manual':
            first_name = request.POST.get('student_first_name')
            last_name = request.POST.get('student_last_name')
            patronymic = request.POST.get('student_patronymic')
            username = slugify(translit(last_name + first_name[0] + patronymic[0], 'ru', reversed=True))
            password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

            try:
                # Записываем имя пользователя и пароль в файл
                file_path = os.path.join(settings.BASE_DIR, 'accounts', f'{group_number}.txt')
                with open(file_path, 'a') as f:
                    f.write(f'{last_name} {first_name} {patronymic} - login: {username}, password: {password}\n')

                # Создаем пользователя и студента
                user = User.objects.create(username=username, password=make_password(password), last_name=last_name,
                                           first_name=first_name, stud_group=group, is_student=True)
                return redirect('accounts:upload_students')
            except Exception as e:
                return redirect('accounts:upload_students')

    else:
        return render(request, 'accounts/upload_students.html')


@user_passes_test(lambda u: u.is_superuser, login_url='login_view')
def user_list(request):
    teachers = User.objects.filter(is_teacher=True)
    students = User.objects.filter(is_student=True)
    groups = User.objects.values_list('stud_group', flat=True).distinct()

    group_filter = request.GET.get('group_filter')
    if group_filter:
        students = students.filter(stud_group=group_filter)

    context = {
        'teachers': teachers,
        'students': students,
        'groups': groups,
        'selected_group': group_filter,
    }

    return render(request, 'accounts/view_users.html', context)


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Аутентификация пользователя
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Если пользователь существует, то выполняем вход
            login(request, user)

            # Проверяем, является ли пользователь администратором, преподавателем
            if user.is_superuser or user.is_teacher:
                return redirect('accounts:teacher_home')
            # Проверяем, является ли пользователь студентом
            elif user.is_student:
                return redirect('accounts:student_home')

        # Если пользователь не найден или пароль неверный, то выводим сообщение об ошибке
        error_message = 'Неверное имя пользователя или пароль'
        return render(request, 'accounts/login.html', {'error_message': error_message})
    else:
        return render(request, 'accounts/login.html')


@user_passes_test(lambda u: u.is_superuser or u.is_teacher, login_url='accounts:login_view')
def teacher_home(request):
    user = request.user
    students_count = 0
    teachers_count = 0
    subjects_count = 0
    tests_count = 0

    if user.is_superuser:
        # Логика для администратора
        students_count = User.objects.filter(is_student=True).count()
        teachers_count = User.objects.filter(is_teacher=True).count()
        subjects_count = Subject.objects.all().count()
        tests_count = Test.objects.all().count()
    else:
        # Логика для преподавателя
        subjects_count = Subject.objects.filter(author=user).count()
        tests_count = Test.objects.filter(author=user).count()

    context = {
        'students_count': students_count,
        'teachers_count': teachers_count,
        'subjects_count': subjects_count,
        'tests_count': tests_count,
    }
    return render(request, 'accounts/teacher_home.html', context)


@user_passes_test(lambda u: u.is_student, login_url='accounts:login_view')
def student_home(request):
    # Подсчет кол-ва доступных тестов
    active_tests = 0
    user = request.user
    tests = Test.objects.all()
    activation_settings = TestActivationSettings.objects.filter(test__in=tests)
    now = datetime.now()
    for test in tests:
        if test.group.number == user.stud_group:
            for activation in activation_settings:
                if activation.test == test and activation.is_active:
                    active_tests += 1


    # Подсчет кол-ва пройденых тестов
    best_attempts = TestAttempt.objects.filter(user=request.user).values('test').annotate(
        max_score=Max('score')
    )
    test_attempts = []
    for attempt in best_attempts:
        best_attempt = TestAttempt.objects.filter(
            user=request.user, test=attempt['test'], score=attempt['max_score']
        ).latest('timestamp')
        test_attempts.append(best_attempt)

    tests_count = len(test_attempts)

    context = {
        'tests_count': tests_count,
        'active_tests': active_tests,
        'tests': tests,
        'activation_settings': activation_settings,
        'now': now
    }
    return render(request, 'accounts/student_home.html', context)


def logout_view(request):
    logout(request)
    return redirect('accounts:login_view')


@login_required
def user_profile(request):
    if request.method == 'POST':
        profile_photo_form = ProfilePhotoForm(request.POST, request.FILES, instance=request.user)
        password_form = ChangePasswordForm(request.user, request.POST)

        if profile_photo_form.is_valid():
            profile_photo_form.save()
            messages.success(request, 'Фото профиля успешно обновлено.')

        if password_form.is_valid():
            password_form.save()
            messages.success(request, 'Пароль успешно изменен.')

    else:
        profile_photo_form = ProfilePhotoForm(instance=request.user)
        password_form = ChangePasswordForm(request.user)

    return render(request, 'accounts/user_profile.html', {
        'profile_photo_form': profile_photo_form,
        'password_form': password_form,
    })
