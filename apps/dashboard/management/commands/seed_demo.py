from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.projects.models import Project
from services.code_generator import CodeGeneratorService


class Command(BaseCommand):
    help = 'Seeds a demo user and initial sample applications (Attendance System, Calculator, To-Do App)'

    def handle(self, *args, **options):
        username = 'demo'
        password = 'demouser123'
        email = 'demo@promptcraft.ai'

        user, created = User.objects.get_or_create(username=username, defaults={'email': email})
        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        user.save()

        if created:
            self.stdout.write(self.style.SUCCESS(f"Created demo user: '{username}' (Password: '{password}')"))
        else:
            self.stdout.write(self.style.WARNING(f"Updated password for demo user '{username}'"))

        # Seed sample project 1: Attendance Management System
        if not Project.objects.filter(user=user, title__icontains='Attendance').exists():
            p1 = Project.objects.create(
                user=user,
                title='Attendance Management System',
                category='Management',
                original_prompt='Build an Attendance Management System with student enrollment, mark present/absent with date selector, real-time statistics, search by name/roll, and CSV export with localStorage persistence.'
            )
            CodeGeneratorService.generate_project(p1)
            self.stdout.write(self.style.SUCCESS(f"Generated sample: {p1.title}"))

        # Seed sample project 2: Scientific Calculator
        if not Project.objects.filter(user=user, title__icontains='Calculator').exists():
            p2 = Project.objects.create(
                user=user,
                title='Modern Scientific Calculator',
                category='Utility',
                original_prompt='Create a sleek scientific calculator featuring arithmetic operations, square root, square, pi, percent calculations, and an interactive calculation history sidebar.'
            )
            CodeGeneratorService.generate_project(p2)
            self.stdout.write(self.style.SUCCESS(f"Generated sample: {p2.title}"))

        self.stdout.write(self.style.SUCCESS("Demo seeding completed successfully!"))
