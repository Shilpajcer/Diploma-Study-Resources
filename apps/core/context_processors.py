from django.conf import settings


def site(request):
    """Makes the site name and feature flags available in every template."""
    return {
        "SITE_NAME": settings.SITE_NAME,
        "FEATURES": settings.FEATURE_FLAGS,
        "DEV_MODE": settings.DEBUG,
    }
