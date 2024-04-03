from django.urls import path
from . import views

app_name = 'tests'

urlpatterns = [
    path('create/subject/', views.create_subject, name='create_subject'),
    path('create/test/', views.create_test, name='create_test'),
    path('', views.view_tests, name='test_list'),
    path('edit/test/<int:test_id>/', views.edit_test, name='edit_test'),
    path('delete/test/<int:test_id>/', views.delete_test, name='delete_test'),
    path('activate/test/<int:test_id>/', views.activate_test, name='activate_test'),
    path('<int:test_id>/', views.take_test, name='take_test'),
    path('results/<int:attempt_id>/', views.test_results, name='test_results'),
    path('all_result/', views.all_results, name='all_results'),
    path('statistic/', views.view_statistics, name='statistic')
]
