from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.http import JsonResponse
from django.contrib import messages
from .forms import PromptForm
from apps.projects.models import Project
from services.code_generator import CodeGeneratorService


PROMPT_TEMPLATES = [
    {
        'title': 'Attendance Management System',
        'category': 'Management',
        'icon': 'fa-clipboard-user',
        'prompt': 'Build an Attendance Management System with student enrollment, mark present/absent with date selector, real-time statistics, search by name/roll, and CSV export with localStorage persistence.'
    },
    {
        'title': 'To-Do & Priority Planner',
        'category': 'Productivity',
        'icon': 'fa-list-check',
        'prompt': 'Create a modern Task and Priority Manager with Low/Medium/High priority tags, due dates, completion checkmarks, search, status filters (All, Active, Completed), and clear-completed.'
    },
    {
        'title': 'Scientific Calculator',
        'category': 'Utility',
        'icon': 'fa-calculator',
        'prompt': 'Create a sleek scientific calculator featuring arithmetic operations, square root, square, pi, percent calculations, and an interactive calculation history sidebar.'
    },
    {
        'title': 'Google Forms-like Form Builder',
        'category': 'Utility',
        'icon': 'fa-square-poll-vertical',
        'prompt': 'Build a visual Drag-and-Add Form Creator with various question types (short text, paragraph, dropdown, checkbox, 5-star rating), live form preview, and JSON schema export.'
    },
    {
        'title': 'Study & Revision Planner',
        'category': 'Education',
        'icon': 'fa-graduation-cap',
        'prompt': 'Build an interactive Study Planner with subject trackers, daily study goals, Pomodoro timer (25 min study / 5 min break) with audio alert, and weekly revision checklist.'
    },
    {
        'title': 'Student Records System',
        'category': 'Management',
        'icon': 'fa-id-card',
        'prompt': 'Create a comprehensive Student Management System to manage student profiles, roll numbers, grades, GPA calculator, filter by department, and quick card view.'
    }
]


@method_decorator(login_required, name='dispatch')
class GenerateAppView(View):
    def get(self, request):
        form = PromptForm()
        initial_prompt = request.GET.get('preset', '')
        if initial_prompt:
            for template in PROMPT_TEMPLATES:
                if template['title'].lower() == initial_prompt.lower():
                    form = PromptForm(initial={
                        'title': template['title'],
                        'category': template['category'],
                        'prompt': template['prompt']
                    })
                    break

        return render(request, 'generator/new.html', {
            'form': form,
            'templates': PROMPT_TEMPLATES
        })

    def post(self, request):
        form = PromptForm(request.POST)
        if form.is_valid():
            title = form.cleaned_data.get('title') or 'Untitled Project'
            category = form.cleaned_data.get('category')
            prompt = form.cleaned_data.get('prompt')

            # Create the project record
            project = Project.objects.create(
                user=request.user,
                title=title,
                category=category,
                original_prompt=prompt,
                status='pending'
            )

            # Generate project code via service
            success = CodeGeneratorService.generate_project(project)

            # Check if this was an AJAX/fetch request
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.headers.get('accept') == 'application/json':
                return JsonResponse({
                    'success': success,
                    'project_id': str(project.id),
                    'redirect_url': f"/projects/{project.id}/",
                    'status': project.status,
                    'error': project.error_message
                })

            if success:
                messages.success(request, f"'{project.title}' generated successfully!")
                return redirect('projects:workspace', project_id=project.id)
            else:
                messages.error(request, f"Generation encountered an issue: {project.error_message}")
                return redirect('projects:workspace', project_id=project.id)

        return render(request, 'generator/new.html', {
            'form': form,
            'templates': PROMPT_TEMPLATES
        })


@method_decorator(login_required, name='dispatch')
class GenerationStatusView(View):
    def get(self, request, project_id):
        project = get_object_or_404(Project, id=project_id, user=request.user)
        return JsonResponse({
            'id': str(project.id),
            'title': project.title,
            'status': project.status,
            'file_count': project.files.count(),
            'version': project.version,
            'error_message': project.error_message,
            'is_finished': project.status in ('completed', 'failed')
        })
