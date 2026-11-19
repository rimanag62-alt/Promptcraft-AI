from django.urls import path, re_path
from . import views

app_name = 'projects'

urlpatterns = [
    path('<uuid:project_id>/', views.ProjectWorkspaceView.as_view(), name='workspace'),
    path('<uuid:project_id>/download/', views.ProjectDownloadZipView.as_view(), name='download_zip'),
    path('<uuid:project_id>/iterate/', views.ProjectIterateView.as_view(), name='iterate'),
    path('<uuid:project_id>/delete/', views.ProjectDeleteView.as_view(), name='delete'),
    
    # File content API endpoint
    path('<uuid:project_id>/files/<path:file_path>', views.ProjectFileContentView.as_view(), name='file_content'),
    
    # Live preview runner endpoints
    path('<uuid:project_id>/preview/', views.ProjectPreviewView.as_view(), name='preview'),
    path('<uuid:project_id>/preview/<path:asset_path>', views.ProjectPreviewView.as_view(), name='preview_asset'),
]
