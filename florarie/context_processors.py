from datetime import datetime

from django.conf import settings


def date_firma(request):
    # Lab 2: datele firmei din settings.py ajung in toate template-urile (footer)
    return {
        'firma': settings.DATE_FIRMA,
        'an_curent': datetime.now().year,
    }


def cos(request):
    # numarul de produse din cos, afisat in meniu pe toate paginile
    return {
        'nr_produse_cos': sum(request.session.get('cos', {}).values()),
    }
