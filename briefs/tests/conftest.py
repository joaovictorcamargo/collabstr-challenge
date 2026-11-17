import pytest


@pytest.fixture(autouse=True)
def _no_https_redirect(settings):
    """Production settings redirect HTTP to HTTPS; the test client speaks plain HTTP."""
    settings.SECURE_SSL_REDIRECT = False


@pytest.fixture(autouse=True)
def _plain_static_storage(settings):
    """Tests don't run collectstatic, so skip the hashed-manifest storage."""
    settings.STORAGES = {
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}
    }
