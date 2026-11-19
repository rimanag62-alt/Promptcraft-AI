import os
import io
import zipfile
from pathlib import Path
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from apps.projects.models import Project, ProjectFile, PromptIteration
from services.file_manager import FileManager
from services.zip_service import ZipService
from services.code_generator import CodeGeneratorService


class PromptCraftCoreTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testdeveloper',
            email='dev@promptcraft.ai',
            password='ComplexPassword123!'
        )
        self.client.login(username='testdeveloper', password='ComplexPassword123!')

    def test_user_authentication_flow(self):
        """Test signup, login, and dashboard access."""
        # Logout
        self.client.logout()
        resp = self.client.get(reverse('dashboard:index'))
        self.assertEqual(resp.status_code, 302)  # Redirects to login

        # Login
        login_resp = self.client.post(reverse('accounts:login'), {
            'username': 'testdeveloper',
            'password': 'ComplexPassword123!'
        })
        self.assertEqual(login_resp.status_code, 302)
        
        # Access dashboard
        dash_resp = self.client.get(reverse('dashboard:index'))
        self.assertEqual(dash_resp.status_code, 200)
        self.assertContains(dash_resp, "My Applications")

    def test_application_generation_and_storage(self):
        """Test generating an application and verifying DB and file persistence."""
        post_data = {
            'title': 'Test Attendance System',
            'category': 'Management',
            'prompt': 'Attendance Management System with student enrollment, mark present/absent with date selector, and CSV export.'
        }
        resp = self.client.post(reverse('generator:new'), post_data)
        self.assertEqual(resp.status_code, 302)

        # Verify Project exists
        project = Project.objects.filter(user=self.user, title__icontains='Attendance').first()
        self.assertIsNotNone(project)
        self.assertEqual(project.status, 'completed')
        self.assertGreaterEqual(project.files.count(), 3)

        # Check required files
        index_file = project.files.filter(relative_path='index.html').first()
        self.assertIsNotNone(index_file)
        self.assertIn("Attendance", index_file.content)

        # Verify disk files exist
        project_dir = FileManager.get_project_dir(project.storage_dir)
        self.assertTrue((project_dir / 'index.html').exists())
        self.assertTrue((project_dir / 'css' / 'styles.css').exists())
        self.assertTrue((project_dir / 'js' / 'app.js').exists())

    def test_path_traversal_protection(self):
        """Security: Verify path traversal attempts are strictly prevented."""
        project = Project.objects.create(
            user=self.user,
            title='Security Test',
            original_prompt='Testing path traversal guards',
            status='completed'
        )

        # Attempt to write outside directory boundary
        with self.assertRaises(PermissionError):
            FileManager.write_file(project.storage_dir, '../../escaped.txt', 'Malicious content')

        with self.assertRaises(PermissionError):
            FileManager.write_file(project.storage_dir, '..\\..\\escaped.txt', 'Malicious content')

        with self.assertRaises(PermissionError):
            FileManager.read_file(project.storage_dir, '../../escaped.txt')

    def test_preview_serving_and_csp_headers(self):
        """Verify preview endpoint serves index.html with Content-Security-Policy headers."""
        project = Project.objects.create(
            user=self.user,
            title='Preview Test App',
            original_prompt='Calculator preview test',
            status='completed'
        )
        CodeGeneratorService.generate_project(project)

        # Request preview
        preview_url = reverse('projects:preview', kwargs={'project_id': project.id})
        resp = self.client.get(preview_url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('Content-Security-Policy', resp.headers)
        self.assertIn("connect-src 'none'", resp.headers['Content-Security-Policy'])
        self.assertIn('text/html', resp.headers['Content-Type'])

    def test_project_iteration(self):
        """Test modifying an existing application with a follow-up prompt."""
        project = Project.objects.create(
            user=self.user,
            title='Iteration Test',
            original_prompt='Initial To-Do List app',
            status='completed'
        )
        CodeGeneratorService.generate_project(project)
        self.assertEqual(project.version, 1)

        # Submit modification
        iterate_url = reverse('projects:iterate', kwargs={'project_id': project.id})
        resp = self.client.post(iterate_url, {'prompt': 'Add export to CSV button and dark theme'})
        self.assertEqual(resp.status_code, 302)

        project.refresh_from_db()
        self.assertEqual(project.version, 2)
        self.assertEqual(project.iterations.count(), 2)

    def test_zip_export_and_secret_exclusion(self):
        """Verify ZIP archive is valid and excludes secrets."""
        project = Project.objects.create(
            user=self.user,
            title='Export Project',
            original_prompt='Export test app',
            status='completed'
        )
        CodeGeneratorService.generate_project(project)

        # Write a dummy secret file into project directory to verify it gets stripped
        secret_file = FileManager.get_project_dir(project.storage_dir) / '.env'
        with open(secret_file, 'w') as f:
            f.write("SECRET_KEY=leaked_secret")

        # Request ZIP download
        zip_url = reverse('projects:download_zip', kwargs={'project_id': project.id})
        resp = self.client.get(zip_url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers['Content-Type'], 'application/zip')

        # Read ZIP contents in-memory
        zf = zipfile.ZipFile(io.BytesIO(resp.content))
        file_list = zf.namelist()
        
        self.assertIn('index.html', file_list)
        # Ensure .env is never included
        self.assertNotIn('.env', file_list)
        self.assertNotIn('.env.local', file_list)

    def test_todo_routing_with_task_information_prompt(self):
        """Verify prompt with 'Task Information' routes to To-Do app, not Form Builder."""
        prompt_text = "Build a To-Do List app called TaskMate. Task Information includes title and status."
        project = Project.objects.create(
            user=self.user,
            title='TaskMate To-Do',
            original_prompt=prompt_text,
            status='pending'
        )
        success = CodeGeneratorService.generate_project(project)
        self.assertTrue(success)
        project.refresh_from_db()
        index_file = project.files.filter(relative_path='index.html').first()
        self.assertIsNotNone(index_file)
        self.assertIn("TaskMate", index_file.content)
        self.assertNotIn("FormFlow", index_file.content)

        # Verify preview of css asset works
        css_url = reverse('projects:preview_asset', kwargs={'project_id': project.id, 'asset_path': 'css/styles.css'})
        resp = self.client.get(css_url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('text/css', resp.headers['Content-Type'])

    def tearDown(self):
        # Clean up any generated project directories
        for p in Project.objects.filter(user=self.user):
            FileManager.delete_project_dir(p.storage_dir)
