from configurations.profile_store import UnsupportedProfileVersion
from ui.i18n import t


def format_startup_error(error: Exception) -> str:
    """Return the user-facing startup failure message."""
    detail = str(error)
    if isinstance(error, UnsupportedProfileVersion):
        detail = t(
            "startup_profile_version_error",
            version=error.version,
            supported_version=error.supported_version,
            path=error.path,
        )
    return t("startup_error_body", detail=detail)
