from taiga.api_schemas import CreateUploadRequest
from taiga.submission_service import validate_upload_request


def test_rejects_path_traversal_upload_name() -> None:
    request = CreateUploadRequest(
        originalName="../secret.txt",
        mediaType="text/plain",
        sizeBytes=10,
        sha256="a" * 64,
    )
    assert validate_upload_request(request) == "path_traversal"


def test_rejects_unsupported_extension() -> None:
    request = CreateUploadRequest(
        originalName="payload.exe",
        mediaType="application/octet-stream",
        sizeBytes=10,
        sha256="a" * 64,
    )
    assert validate_upload_request(request) == "extension_not_allowed"


def test_accepts_safe_upload_metadata() -> None:
    request = CreateUploadRequest(
        originalName="answer.md",
        mediaType="text/markdown",
        sizeBytes=10,
        sha256="a" * 64,
    )
    assert validate_upload_request(request) is None
