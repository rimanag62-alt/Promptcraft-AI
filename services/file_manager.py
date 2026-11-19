import os
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from django.conf import settings


class FileManager:
    """
    Manages safe disk operations for generated projects.
    Enforces strict path traversal guards.
    """

    @staticmethod
    def get_base_dir() -> Path:
        base = Path(settings.MEDIA_ROOT) / 'generated_projects'
        base.mkdir(parents=True, exist_ok=True)
        return base.resolve()

    @classmethod
    def get_project_dir(cls, storage_dir: str) -> Path:
        base_dir = cls.get_base_dir()
        target_dir = (base_dir / storage_dir).resolve()
        
        # Security: Prevent escaping outside the designated storage root
        if not cls.is_safe_path(base_dir, target_dir):
            raise PermissionError(f"Access denied: Path '{storage_dir}' escapes base directory.")
            
        target_dir.mkdir(parents=True, exist_ok=True)
        return target_dir

    @classmethod
    def is_safe_path(cls, base_dir: Path, target_path: Path) -> bool:
        """Verifies target_path is strictly inside base_dir."""
        try:
            return target_path.resolve().is_relative_to(base_dir.resolve())
        except AttributeError:
            # Python < 3.9 fallback
            try:
                common = os.path.commonpath([str(base_dir.resolve()), str(target_path.resolve())])
                return common == str(base_dir.resolve())
            except ValueError:
                return False

    @classmethod
    def write_file(cls, storage_dir: str, relative_path: str, content: str) -> Path:
        """Safely writes a file to the project folder."""
        project_dir = cls.get_project_dir(storage_dir)
        # Normalize relative path (strip leading slashes)
        clean_rel_path = relative_path.lstrip('/\\').replace('\\', '/')
        file_path = (project_dir / clean_rel_path).resolve()

        if not cls.is_safe_path(project_dir, file_path):
            raise PermissionError(f"Security error: '{relative_path}' attempts path traversal.")

        # Ensure parent directories exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return file_path

    @classmethod
    def read_file(cls, storage_dir: str, relative_path: str) -> Optional[str]:
        """Safely reads a file from the project folder."""
        project_dir = cls.get_project_dir(storage_dir)
        clean_rel_path = relative_path.lstrip('/\\').replace('\\', '/')
        file_path = (project_dir / clean_rel_path).resolve()

        if not cls.is_safe_path(project_dir, file_path):
            raise PermissionError(f"Security error: '{relative_path}' attempts path traversal.")

        if not file_path.exists() or not file_path.is_file():
            return None

        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()

    @classmethod
    def delete_project_dir(cls, storage_dir: str) -> bool:
        """Safely deletes an entire project folder."""
        try:
            project_dir = cls.get_project_dir(storage_dir)
            if project_dir.exists():
                shutil.rmtree(project_dir)
            return True
        except Exception:
            return False

    @classmethod
    def get_directory_tree(cls, storage_dir: str) -> List[Dict[str, Any]]:
        """
        Returns a hierarchical list/tree of directories and files for the UI treeview.
        """
        project_dir = cls.get_project_dir(storage_dir)
        
        def build_tree(current_dir: Path) -> List[Dict[str, Any]]:
            items = []
            try:
                for entry in sorted(current_dir.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower())):
                    if entry.name.startswith('.'):
                        continue
                    
                    rel_path = entry.relative_to(project_dir).as_posix()
                    if entry.is_dir():
                        items.append({
                            'name': entry.name,
                            'path': rel_path,
                            'type': 'directory',
                            'children': build_tree(entry)
                        })
                    else:
                        ext = entry.suffix.lstrip('.').lower()
                        items.append({
                            'name': entry.name,
                            'path': rel_path,
                            'type': 'file',
                            'extension': ext,
                            'size': entry.stat().st_size
                        })
            except Exception:
                pass
            return items

        return build_tree(project_dir)
