import uuid
from pathlib import Path
from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


class Project(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('generating', 'Generating'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, blank=True)
    original_prompt = models.TextField()
    description = models.TextField(blank=True)
    category = models.CharField(max_length=100, default='General Application')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    storage_dir = models.CharField(max_length=500, blank=True)
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title) or 'project'
            self.slug = f"{base_slug}-{str(self.id)[:8]}"
        if not self.storage_dir:
            self.storage_dir = str(self.id)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} (v{self.version}) - {self.user.username}"

    @property
    def file_count(self):
        return self.files.count()

    def get_entrypoint_file(self):
        """Returns the primary preview file (e.g., index.html)."""
        return self.files.filter(relative_path='index.html').first() or self.files.filter(file_type='html').first()


class ProjectFile(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='files')
    relative_path = models.CharField(max_length=500)
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=50)
    content = models.TextField()
    file_size = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['relative_path']
        unique_together = ('project', 'relative_path')

    def save(self, *args, **kwargs):
        if self.content:
            self.file_size = len(self.content.encode('utf-8'))
        if not self.file_name and self.relative_path:
            self.file_name = Path(self.relative_path).name
        if not self.file_type and self.relative_path:
            ext = Path(self.relative_path).suffix.lstrip('.').lower()
            ext_map = {
                'html': 'html',
                'css': 'css',
                'js': 'javascript',
                'json': 'json',
                'md': 'markdown',
                'txt': 'text',
                'svg': 'svg',
            }
            self.file_type = ext_map.get(ext, ext or 'text')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.project.title}: {self.relative_path}"


class PromptIteration(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='iterations')
    iteration_number = models.PositiveIntegerField()
    prompt = models.TextField()
    summary_of_changes = models.TextField(blank=True)
    model_used = models.CharField(max_length=100, default='gemini-2.5-flash')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.project.title} - Iteration #{self.iteration_number}"
