from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('upload_teachers/', views.upload_teachers, name='upload_teachers'),
    path('upload_students/', views.upload_students, name='upload_students'),
    path('user_list/', views.user_list, name='user_list'),
    path('', views.login_view, name='login_view'),
    path('logout/', views.logout_view, name='logout'),
    path('teacher_home/', views.teacher_home, name='teacher_home'),
    path('student_home/', views.student_home, name='student_home'),
    path('profile/', views.user_profile, name='user_profile')
]
