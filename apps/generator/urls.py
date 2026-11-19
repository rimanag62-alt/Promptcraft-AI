from django.urls import path
from . import views

app_name = 'generator'

urlpatterns = [
    path('generate/', views.GenerateAppView.as_view(), name='new'),
    path('generate/status/<uuid:project_id>/', views.GenerationStatusView.as_view(), name='status'),
]
