from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.db.models import Q
from apps.projects.models import Project


class HomeView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard:index')
        return render(request, 'dashboard/home.html')


@method_decorator(login_required, name='dispatch')
class DashboardView(View):
    def get(self, request):
        query = request.GET.get('q', '').strip()
        category = request.GET.get('category', '').strip()

        projects = Project.objects.filter(user=request.user)

        if query:
            projects = projects.filter(
                Q(title__icontains=query) |
                Q(original_prompt__icontains=query) |
                Q(description__icontains=query)
            )

        if category and category != 'All':
            projects = projects.filter(category__iexact=category)

        total_count = Project.objects.filter(user=request.user).count()
        completed_count = Project.objects.filter(user=request.user, status='completed').count()

        # Unique categories for filter pills
        categories = Project.objects.filter(user=request.user).values_list('category', flat=True).distinct()
        categories = [c for c in categories if c]

        return render(request, 'dashboard/index.html', {
            'projects': projects,
            'query': query,
            'selected_category': category,
            'categories': categories,
            'total_count': total_count,
            'completed_count': completed_count,
        })
