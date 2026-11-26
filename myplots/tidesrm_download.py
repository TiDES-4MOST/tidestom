"""Download TiDES-RM products using tokens independent of TOM accounts."""

import hashlib
import hmac
import logging
import re
import shutil
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, HttpResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET


logger = logging.getLogger(__name__)


def _authorized(request):
    scheme, separator, token = request.headers.get("Authorization", "").partition(" ")
    if scheme.lower() != "bearer" or not separator or not token or not token.isascii():
        return False
    digest = hashlib.sha256(token.encode("ascii")).hexdigest()
    # Evaluate every comparison, rather than returning on the first match.
    matches = [hmac.compare_digest(digest, configured) for configured in settings.TIDESRM_TOKEN_SHA256]
    return any(matches)


@never_cache
@require_GET
def download_tidesrm_by_date(request, obsdate):
    """Return the matching original FITS file, or a ZIP if several match."""
    if not settings.TIDESRM_TOKEN_SHA256 or not all(
        re.fullmatch(r"[0-9a-f]{64}", digest) for digest in settings.TIDESRM_TOKEN_SHA256
    ):
        return HttpResponse("Download service not configured.", status=503, content_type="text/plain")
    if not _authorized(request):
        response = HttpResponse("Invalid or missing token.", status=401, content_type="text/plain")
        response["WWW-Authenticate"] = 'Bearer realm="TiDES-RM downloads"'
        return response

    if not re.fullmatch(r"[0-9]{8}", obsdate):
        return HttpResponse("Date must be YYYYMMDD.", status=400, content_type="text/plain")
    try:
        datetime.strptime(obsdate, "%Y%m%d")
    except ValueError:
        return HttpResponse("Invalid observing date.", status=400, content_type="text/plain")

    process_env = request.GET.get("process_env", "operations")
    if process_env not in ("operations", "reproc"):
        return HttpResponse("Invalid process environment.", status=400, content_type="text/plain")

    root = Path(settings.TIDESRM_DOWNLOAD_ROOT)
    env_dir = root / process_env
    date_dir = env_dir / obsdate
    try:
        if not root.is_dir():
            return HttpResponse("Download storage unavailable.", status=503, content_type="text/plain")
        # Refuse symlinks in the served hierarchy, including individual files.
        if env_dir.is_symlink() or date_dir.is_symlink():
            return HttpResponse("No files found.", status=404, content_type="text/plain")
        if not date_dir.is_dir():
            return HttpResponse("No files found.", status=404, content_type="text/plain")

        pattern = re.compile(rf"{obsdate}_LJ11_[0-9]{{8}}_S1003\.fits\Z")
        files = sorted(
            path for path in date_dir.iterdir()
            if pattern.fullmatch(path.name) and not path.is_symlink() and path.is_file()
        )
        if not files:
            return HttpResponse("No files found.", status=404, content_type="text/plain")

        if len(files) == 1:
            response = FileResponse(files[0].open("rb"), as_attachment=True, filename=files[0].name)
        else:
            archive = tempfile.TemporaryFile()
            try:
                with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_STORED, allowZip64=True) as zipped:
                    for path in files:
                        with path.open("rb") as source, zipped.open(path.name, "w", force_zip64=True) as dest:
                            shutil.copyfileobj(source, dest)
                archive.seek(0)
                response = FileResponse(
                    archive, as_attachment=True,
                    filename=f"tidesrm_{process_env}_{obsdate}.zip",
                    content_type="application/zip",
                )
            except Exception:
                archive.close()
                raise
    except OSError:
        logger.exception("Unable to read TiDES-RM download for date %s", obsdate)
        return HttpResponse("Download storage unavailable.", status=503, content_type="text/plain")

    response["X-Content-Type-Options"] = "nosniff"
    return response