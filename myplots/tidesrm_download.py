"""Download survey products using tokens independent of TOM accounts."""

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


def _authorized(request, token_hashes):
    scheme, separator, token = request.headers.get("Authorization", "").partition(" ")
    if scheme.lower() != "bearer" or not separator or not token or not token.isascii():
        return False
    digest = hashlib.sha256(token.encode("ascii")).hexdigest()
    # Evaluate every comparison, rather than returning on the first match.
    matches = [hmac.compare_digest(digest, configured) for configured in token_hashes]
    return any(matches)


@never_cache
@require_GET
def download_tidesrm_by_date(request, obsdate):
    """Return the matching original FITS file, or a ZIP if several match."""
    return _download_by_date(
        request, obsdate, settings.TIDESRM_TOKEN_SHA256, settings.TIDESRM_DOWNLOAD_ROOT,
        survey_id="S1003", label="tidesrm", realm="TiDES-RM downloads",
    )


@never_cache
@require_GET
def download_4slsls_by_date(request, obsdate):
    """Return the 4SLSLS FITS file or ZIP for an observing date."""
    return _download_by_date(
        request, obsdate, settings.FOURSLSLS_TOKEN_SHA256, settings.FOURSLSLS_DOWNLOAD_ROOT,
        survey_id="S1004", label="4slsls", realm="4SLSLS downloads",
    )


def _download_by_date(request, obsdate, token_hashes, download_root, *, survey_id, label, realm):
    if not token_hashes or not all(
        re.fullmatch(r"[0-9a-f]{64}", digest) for digest in token_hashes
    ):
        return HttpResponse("Download service not configured.", status=503, content_type="text/plain")
    if not _authorized(request, token_hashes):
        response = HttpResponse("Invalid or missing token.", status=401, content_type="text/plain")
        response["WWW-Authenticate"] = f'Bearer realm="{realm}"'
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

    root = Path(download_root)
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

        pattern = re.compile(rf"{obsdate}_LJ11_[0-9]{{8}}_QTR_{re.escape(survey_id)}\.fits\Z")
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
                    filename=f"{label}_{process_env}_{obsdate}.zip",
                    content_type="application/zip",
                )
            except Exception:
                archive.close()
                raise
    except OSError:
        logger.exception("Unable to read %s download for date %s", label, obsdate)
        return HttpResponse("Download storage unavailable.", status=503, content_type="text/plain")

    response["X-Content-Type-Options"] = "nosniff"
    return response