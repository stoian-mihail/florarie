from .views import Accesare, ACCESARI


def get_ip(request):
    str_lista_ip = request.META.get('HTTP_X_FORWARDED_FOR')
    if str_lista_ip:
        return str_lista_ip.split(',')[-1].strip()
    else:
        return request.META.get('REMOTE_ADDR')


# cereri pe care nu le consideram accesari de pagini ale site-ului
PREFIXE_IGNORATE = ('/static/', '/media/', '/admin/', '/favicon.ico')


class AccesareMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Lab 1: ip-ul utilizatorului, folosit apoi in view-uri si in footer
        request.ip_client = get_ip(request)

        # Lab 1: la fiecare cerere de vizualizare a unei pagini cream o Accesare
        if not request.path.startswith(PREFIXE_IGNORATE):
            accesare = Accesare(
                ip_client=request.ip_client,
                url=request.build_absolute_uri(),
                parametri={cheie: request.GET.getlist(cheie) for cheie in request.GET},
            )
            ACCESARI.append(accesare)
            request.accesare = accesare  # folosita in /info pentru data serverului
            print(accesare)

        return self.get_response(request)
