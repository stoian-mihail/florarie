from datetime import datetime

from django.conf import settings


def date_firma(request):
    # Lab 2: datele firmei din settings.py ajung in toate template-urile (footer)
    return {
        'firma': settings.DATE_FIRMA,
        'an_curent': datetime.now().year,
    }
