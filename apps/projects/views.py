import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.http import HttpResponse, JsonResponse, Http404
from django.contrib import messages
from django.views.decorators.clickjacking import xframe_options_sameorigin
from .models import Project, ProjectFile, PromptIteration
from services.file_manager import FileManager
from services.zip_service import ZipService
from services.sandbox_service import SandboxService
from services.code_generator import CodeGeneratorService


@method_decorator(login_required, name='dispatch')
class ProjectWorkspaceView(View):
    def get(self, request, project_id):
        project = get_object_or_404(Project, id=project_id, user=request.user)
        files = project.files.all().order_by('relative_path')
        
        # Pick default active file (index.html if available)
        active_file = project.get_entrypoint_file() or files.first()
        tree = FileManager.get_directory_tree(project.storage_dir)
        iterations = project.iterations.all().order_by('-iteration_number')

        return render(request, 'projects/workspace.html', {
            'project': project,
            'files': files,
            'active_file': active_file,
            'directory_tree': tree,
            'iterations': iterations,
        })


@method_decorator(login_required, name='dispatch')
class ProjectFileContentView(View):
    def get(self, request, project_id, file_path):
        project = get_object_or_404(Project, id=project_id, user=request.user)
        clean_path = file_path.lstrip('/\\').replace('\\', '/')
        
        project_file = project.files.filter(relative_path=clean_path).first()
        if not project_file:
            # Fallback to reading disk
            content = FileManager.read_file(project.storage_dir, clean_path)
            if content is None:
                return JsonResponse({'error': f"File '{clean_path}' not found."}, status=404)
            file_type = clean_path.split('.')[-1]
            return JsonResponse({
                'relative_path': clean_path,
                'file_name': clean_path.split('/')[-1],
                'file_type': file_type,
                'content': content,
                'file_size': len(content.encode('utf-8'))
            })

        return JsonResponse({
            'relative_path': project_file.relative_path,
            'file_name': project_file.file_name,
            'file_type': project_file.file_type,
            'content': project_file.content,
            'file_size': project_file.file_size
        })


class ProjectPreviewView(View):
    """
    Serves project assets safely inside the workspace sandbox iframe.
    Available to authenticated user owner or within project preview session.
    """
    @xframe_options_sameorigin
    def get(self, request, project_id, asset_path='index.html'):
        project = get_object_or_404(Project, id=project_id)
        if request.user.is_authenticated and project.user != request.user:
            return HttpResponse("Forbidden", status=403)

        return SandboxService.serve_preview_asset(project.storage_dir, asset_path)


@method_decorator(login_required, name='dispatch')
class ProjectDownloadZipView(View):
    def get(self, request, project_id):
        project = get_object_or_404(Project, id=project_id, user=request.user)
        
        zip_buffer = ZipService.create_project_zip_buffer(
            storage_dir=project.storage_dir,
            project_title=project.title
        )

        filename = f"{project.slug or 'project'}.zip"
        response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['Content-Length'] = len(zip_buffer.getvalue())
        return response


@method_decorator(login_required, name='dispatch')
class ProjectIterateView(View):
    def post(self, request, project_id):
        project = get_object_or_404(Project, id=project_id, user=request.user)
        modification_prompt = request.POST.get('prompt', '').strip()

        if not modification_prompt:
            messages.error(request, "Modification prompt cannot be empty.")
            return redirect('projects:workspace', project_id=project.id)

        success = CodeGeneratorService.iterate_project(project, modification_prompt)
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.headers.get('accept') == 'application/json':
            return JsonResponse({
                'success': success,
                'version': project.version,
                'error': project.error_message,
                'redirect_url': f"/projects/{project.id}/"
            })

        if success:
            messages.success(request, f"Updated application to version {project.version}!")
        else:
            messages.error(request, f"Update encountered an issue: {project.error_message}")

        return redirect('projects:workspace', project_id=project.id)


@method_decorator(login_required, name='dispatch')
class ProjectDeleteView(View):
    def get(self, request, project_id):
        project = get_object_or_404(Project, id=project_id, user=request.user)
        return render(request, 'projects/confirm_delete.html', {'project': project})

    def post(self, request, project_id):
        project = get_object_or_404(Project, id=project_id, user=request.user)
        title = project.title
        
        # Clean up files on disk
        FileManager.delete_project_dir(project.storage_dir)
        # Delete DB record (cascades to files and iterations)
        project.delete()

        messages.success(request, f"Project '{title}' has been deleted.")
        return redirect('dashboard:index')
