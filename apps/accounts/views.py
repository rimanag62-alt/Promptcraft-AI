from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views import View
from django.utils.decorators import method_decorator
from .forms import SignUpForm, LoginForm
from apps.projects.models import Project


class SignUpView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard:index')
        form = SignUpForm()
        return render(request, 'accounts/signup.html', {'form': form})

    def set_user(self, form):
        user = form.save(commit=False)
        user.set_password(form.cleaned_data['password'])
        user.save()
        return user

    def post(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard:index')
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = self.set_user(form)
            login(request, user)
            messages.success(request, f"Welcome to PromptCraft AI, {user.username}!")
            return redirect('dashboard:index')
        return render(request, 'accounts/signup.html', {'form': form})


class LoginView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard:index')
        form = LoginForm()
        return render(request, 'accounts/login.html', {'form': form})

    def post(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard:index')
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            next_url = request.GET.get('next') or 'dashboard:index'
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password. Please try again.")
        return render(request, 'accounts/login.html', {'form': form})


class LogoutView(View):
    def get(self, request):
        logout(request)
        messages.info(request, "You have been logged out.")
        return redirect('accounts:login')

    def post(self, request):
        logout(request)
        messages.info(request, "You have been logged out.")
        return redirect('accounts:login')


@method_decorator(login_required, name='dispatch')
class ProfileView(View):
    def get(self, request):
        user_projects = Project.objects.filter(user=request.user)
        total_projects = user_projects.count()
        completed_projects = user_projects.filter(status='completed').count()
        return render(request, 'accounts/profile.html', {
            'user': request.user,
            'total_projects': total_projects,
            'completed_projects': completed_projects,
        })
