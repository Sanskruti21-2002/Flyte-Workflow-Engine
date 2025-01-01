
from django.urls import path
from . import views

urlpatterns = [
    path("", views.new_page, name="new_page"),  # Default to new_page.html
    path('trigger_workflow/', views.trigger_workflow, name='trigger_workflow'),  # Trigger workflow logic
    path('delete_file/', views.delete_file, name='delete_file'),
    path('services/', views.get_folders, name='services'),  # Map services to get_folders (base.html)
    path('home/', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('terminate/', views.terminate_view, name='terminate'),
    path('recover/', views.recover_view, name='recover'),
    path('relaunch/', views.relaunch_view, name='relaunch'),
    path('fetch-running-executions/', views.fetch_running_executions_view, name='fetch_running_executions'),
    path('fetch_logs/', views.fetch_logs, name='fetch_logs'),

] 

