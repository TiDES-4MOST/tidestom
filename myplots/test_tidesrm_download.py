import hashlib
import io
import tempfile
import zipfile
from pathlib import Path

from django.test import RequestFactory, SimpleTestCase, override_settings
from django.urls import resolve

from myplots.tidesrm_download import download_4slsls_by_date, download_tidesrm_by_date


TOKEN = "test-token"
TOKEN_HASH = hashlib.sha256(TOKEN.encode()).hexdigest()


class TestTidesRMDownload(SimpleTestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        self.settings_override = override_settings(
            TIDESRM_DOWNLOAD_ROOT=str(self.root), TIDESRM_TOKEN_SHA256=(TOKEN_HASH,)
        )
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        self.factory = RequestFactory()

    def request(self, date="20260202", *, token=TOKEN, query="", method="get"):
        headers = {} if token is None else {"HTTP_AUTHORIZATION": f"Bearer {token}"}
        request = getattr(self.factory, method)(f"/api/tidesrm/download/{date}/{query}", **headers)
        return download_tidesrm_by_date(request, date)

    def put_file(self, name="20260202_LJ11_20260209_QTR_S1003.fits", *, env="operations", data=b"FITS"):
        directory = self.root / env / "20260202"
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / name
        path.write_bytes(data)
        return path

    def read_response(self, response):
        try:
            return b"".join(response.streaming_content)
        finally:
            response.close()

    def test_url_resolves(self):
        match = resolve("/api/tidesrm/download/20260202/")
        self.assertEqual(match.url_name, "download_tidesrm_by_date")

    def test_missing_and_invalid_token(self):
        self.put_file()
        for token in (None, "wrong"):
            response = self.request(token=token)
            self.assertEqual(response.status_code, 401)
            self.assertIn("Bearer", response["WWW-Authenticate"])

    @override_settings(TIDESRM_TOKEN_SHA256=())
    def test_no_tokens_fails_closed(self):
        self.assertEqual(self.request().status_code, 503)

    @override_settings(TIDESRM_TOKEN_SHA256=("not-a-digest",))
    def test_invalid_token_configuration_fails_closed(self):
        self.assertEqual(self.request().status_code, 503)

    def test_multiple_tokens_can_be_revoked_independently(self):
        second = hashlib.sha256(b"second-token").hexdigest()
        self.put_file()
        with override_settings(TIDESRM_TOKEN_SHA256=(TOKEN_HASH, second)):
            self.assertEqual(self.read_response(self.request(token="second-token")), b"FITS")
        self.assertEqual(self.request(token="second-token").status_code, 401)

    def test_single_file_returns_original_bytes(self):
        path = self.put_file(data=b"original fits bytes")
        response = self.request()
        self.assertEqual(response.status_code, 200)
        self.assertIn(path.name, response["Content-Disposition"])
        self.assertIn("no-store", response["Cache-Control"])
        self.assertEqual(self.read_response(response), b"original fits bytes")

    def test_multiple_matches_return_zip_without_unrelated_files(self):
        first = self.put_file(data=b"first")
        second = self.put_file("20260202_LJ11_20260210_QTR_S1003.fits", data=b"second")
        self.put_file("20260202_LJ11_20260210_QTR_S1004.fits", data=b"other")
        response = self.request()
        self.assertEqual(response["Content-Type"], "application/zip")
        self.assertIn("tidesrm_operations_20260202.zip", response["Content-Disposition"])
        with zipfile.ZipFile(io.BytesIO(self.read_response(response))) as archive:
            self.assertEqual(archive.namelist(), [first.name, second.name])
            self.assertEqual(archive.read(first.name), b"first")
            self.assertEqual(archive.read(second.name), b"second")

    def test_reproc_must_be_explicitly_requested(self):
        self.put_file(env="reproc", data=b"reprocessed")
        self.assertEqual(self.request().status_code, 404)
        self.assertEqual(self.read_response(self.request(query="?process_env=reproc")), b"reprocessed")

    def test_invalid_inputs_and_missing_files(self):
        for date in ("20260230", "2026-02-02", "2026020"):
            self.assertEqual(self.request(date).status_code, 400)
        self.assertEqual(self.request(query="?process_env=../operations").status_code, 400)
        self.assertEqual(self.request().status_code, 404)
        self.assertEqual(self.request(method="post").status_code, 405)

    def test_missing_storage_returns_503(self):
        with override_settings(TIDESRM_DOWNLOAD_ROOT=str(self.root / "missing")):
            self.assertEqual(self.request().status_code, 503)

    def test_symlinks_are_not_downloaded(self):
        external = self.root / "secret"
        external.write_bytes(b"secret")
        path = self.put_file()
        path.unlink()
        path.symlink_to(external)
        self.assertEqual(self.request().status_code, 404)

    def test_symlinked_date_directory_is_not_used(self):
        real_dir = self.root / "real"
        real_dir.mkdir()
        (real_dir / "20260202_LJ11_20260209_QTR_S1003.fits").write_bytes(b"secret")
        env_dir = self.root / "operations"
        env_dir.mkdir()
        (env_dir / "20260202").symlink_to(real_dir, target_is_directory=True)
        self.assertEqual(self.request().status_code, 404)


class Test4SLSLSDownload(TestTidesRMDownload):
    def setUp(self):
        super().setUp()
        self.tidesrm_root = self.root
        self.root = self.root / "4slsls"
        self.root.mkdir()
        self.fourslsls_token = "4slsls-test-token"
        self.fourslsls_hash = hashlib.sha256(self.fourslsls_token.encode()).hexdigest()
        override = override_settings(
            FOURSLSLS_DOWNLOAD_ROOT=str(self.root), FOURSLSLS_TOKEN_SHA256=(self.fourslsls_hash,)
        )
        override.enable()
        self.addCleanup(override.disable)

    def request(self, date="20260202", *, token="4slsls-test-token", query="", method="get"):
        headers = {} if token is None else {"HTTP_AUTHORIZATION": f"Bearer {token}"}
        request = getattr(self.factory, method)(f"/api/4slsls/download/{date}/{query}", **headers)
        return download_4slsls_by_date(request, date)

    def put_file(self, name="20260202_LJ11_20260209_QTR_S1004.fits", *, env="operations", data=b"FITS"):
        return super().put_file(name, env=env, data=data)

    def test_url_resolves(self):
        match = resolve("/api/4slsls/download/20260202/")
        self.assertEqual(match.url_name, "download_4slsls_by_date")

    @override_settings(FOURSLSLS_TOKEN_SHA256=())
    def test_no_tokens_fails_closed(self):
        self.assertEqual(self.request().status_code, 503)

    @override_settings(FOURSLSLS_TOKEN_SHA256=("not-a-digest",))
    def test_invalid_token_configuration_fails_closed(self):
        self.assertEqual(self.request().status_code, 503)

    def test_multiple_tokens_can_be_revoked_independently(self):
        second = hashlib.sha256(b"second-token").hexdigest()
        self.put_file()
        with override_settings(FOURSLSLS_TOKEN_SHA256=(self.fourslsls_hash, second)):
            self.assertEqual(self.read_response(self.request(token="second-token")), b"FITS")
        self.assertEqual(self.request(token="second-token").status_code, 401)

    def test_missing_storage_returns_503(self):
        with override_settings(FOURSLSLS_DOWNLOAD_ROOT=str(self.root / "missing")):
            self.assertEqual(self.request().status_code, 503)

    def test_multiple_matches_return_zip_without_unrelated_files(self):
        first = self.put_file(data=b"first")
        second = self.put_file("20260202_LJ11_20260210_QTR_S1004.fits", data=b"second")
        self.put_file("20260202_LJ11_20260210_QTR_S1003.fits", data=b"other")
        response = self.request()
        self.assertEqual(response["Content-Type"], "application/zip")
        self.assertIn("4slsls_operations_20260202.zip", response["Content-Disposition"])
        with zipfile.ZipFile(io.BytesIO(self.read_response(response))) as archive:
            self.assertEqual(archive.namelist(), [first.name, second.name])
            self.assertEqual(archive.read(first.name), b"first")
            self.assertEqual(archive.read(second.name), b"second")

    def test_survey_tokens_are_not_interchangeable(self):
        self.put_file()
        self.assertEqual(self.request(token=TOKEN).status_code, 401)
        request = self.factory.get(
            "/api/tidesrm/download/20260202/", HTTP_AUTHORIZATION=f"Bearer {self.fourslsls_token}"
        )
        self.assertEqual(download_tidesrm_by_date(request, "20260202").status_code, 401)

    def test_unconfigured_survey_does_not_disable_other(self):
        self.put_file()
        with override_settings(TIDESRM_TOKEN_SHA256=()):
            self.assertEqual(self.read_response(self.request()), b"FITS")
