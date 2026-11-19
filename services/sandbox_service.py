import mimetypes
from pathlib import Path
from typing import Optional, Tuple
from django.http import HttpResponse, Http404
from .file_manager import FileManager


class SandboxService:
    """
    Handles secure delivery of generated web application assets to preview iframes.
    Enforces strict Content-Security-Policy to isolate execution.
    """

    CSP_HEADER = (
        "default-src 'self' 'unsafe-inline' data: blob: "
        "https://cdnjs.cloudflare.com https://fonts.googleapis.com https://fonts.gstatic.com; "
        "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
        "font-src 'self' data: https://cdnjs.cloudflare.com https://fonts.gstatic.com; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdnjs.cloudflare.com; "
        "img-src 'self' data: blob: https:; "
        "connect-src 'none'; "
        "frame-ancestors 'self';"
    )

    @classmethod
    def serve_preview_asset(cls, storage_dir: str, asset_path: str = "index.html") -> HttpResponse:
        """
        Serves a file from the project directory with security headers and correct MIME type.
        """
        if not asset_path or asset_path == '/':
            asset_path = 'index.html'

        clean_path = asset_path.lstrip('/\\')
        content = FileManager.read_file(storage_dir, clean_path)

        if content is None:
            raise Http404(f"Asset '{asset_path}' not found in project workspace.")

        # Determine MIME type
        content_type, _ = mimetypes.guess_type(clean_path)
        if clean_path.endswith('.css'):
            content_type = 'text/css; charset=utf-8'
        elif clean_path.endswith('.js'):
            content_type = 'application/javascript; charset=utf-8'
        elif clean_path.endswith('.html') or clean_path.endswith('.htm'):
            content_type = 'text/html; charset=utf-8'
        elif clean_path.endswith('.json'):
            content_type = 'application/json; charset=utf-8'
        elif not content_type:
            content_type = 'text/plain; charset=utf-8'

        response = HttpResponse(content, content_type=content_type)

        # Security Headers
        response['Content-Security-Policy'] = cls.CSP_HEADER
        response['X-Content-Type-Options'] = 'nosniff'
        response['Referrer-Policy'] = 'no-referrer'
        # Prevent caching inside dev workspace so preview reflects immediate updates
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'

        return response
