from pathlib import Path

from django.conf import settings

CSS_DIR = Path(settings.BASE_DIR) / 'static' / 'css'


def asset_version(request):
    """
    `?v=<asset_version>` on CSS links: changes whenever a stylesheet is edited, so
    browsers fetch the new file instead of showing a stale cached copy.
    """
    try:
        version = int(max(f.stat().st_mtime for f in CSS_DIR.glob('*.css')))
    except (OSError, ValueError):
        version = 0
    return {'asset_version': version}
