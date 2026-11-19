import io
import zipfile
from pathlib import Path
from django.conf import settings
from .file_manager import FileManager


class ZipService:
    """
    Creates downloadable ZIP archives of generated projects.
    Excludes sensitive files and environment variables.
    """

    # Forbidden file names and patterns that must never be packaged
    EXCLUDED_PATTERNS = {
        '.env', '.env.local', '.env.production',
        '.git', '.gitignore',
        '__pycache__', '.pytest_cache',
        'id_rsa', 'id_rsa.pub', '.key', '.pem',
        'thumbs.db', '.ds_store'
    }

    @classmethod
    def should_exclude(cls, file_path: Path) -> bool:
        name_lower = file_path.name.lower()
        if name_lower in cls.EXCLUDED_PATTERNS:
            return True
        for part in file_path.parts:
            if part.lower() in cls.EXCLUDED_PATTERNS or part.startswith('.'):
                return True
        return False

    @classmethod
    def create_project_zip_buffer(cls, storage_dir: str, project_title: str = "project") -> io.BytesIO:
        """
        Creates an in-memory ZIP archive from the project directory.
        Returns a BytesIO stream ready for Django FileResponse / HttpResponse.
        """
        project_dir = FileManager.get_project_dir(storage_dir)
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path in project_dir.rglob('*'):
                if file_path.is_file():
                    if cls.should_exclude(file_path):
                        continue
                    
                    # Store with relative path inside archive
                    archive_name = file_path.relative_to(project_dir).as_posix()
                    zf.write(file_path, arcname=archive_name)

        zip_buffer.seek(0)
        return zip_buffer
