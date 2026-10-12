from datetime import datetime
from urllib.parse import urlparse

from django.http import HttpResponse


# Lab 1: data in limba romana

ZILE = ['Luni', 'Marți', 'Miercuri', 'Joi', 'Vineri', 'Sâmbătă', 'Duminică']
LUNI = ['Ianuarie', 'Februarie', 'Martie', 'Aprilie', 'Mai', 'Iunie',
        'Iulie', 'August', 'Septembrie', 'Octombrie', 'Noiembrie', 'Decembrie']

# formatul cerut: [zi din saptamana], [zi din luna] [numele lunii] [an] -> Joi, 2 Octombrie 2025
FORMAT_ZI = '%A, %-d %B %Y'
FORMAT_TIMP = '%H:%M:%S'


def formateaza_data(data, format=FORMAT_ZI):
    # functie comuna, folosita si de /info si de clasa Accesare (ca sa nu avem codul in 2 locuri)
    # %A si %B sunt inlocuite cu valorile din liste de la indicii respectivi, iar %-d cu ziua din luna
    format = (format.replace('%A', ZILE[data.weekday()])
                    .replace('%B', LUNI[data.month - 1])
                    .replace('%-d', str(data.day)))
    return data.strftime(format)


# Lab 1: clasa Accesare

class Accesare:
    ultimul_id = 0  # contor comun pentru toate instantele -> id autoincrementat

    def __init__(self, ip_client, url, parametri=None, data=None):
        Accesare.ultimul_id += 1
        self.id = Accesare.ultimul_id
        self.ip_client = ip_client
        self.url = url
        # nu punem {} direct ca valoare implicita: ar fi acelasi dictionar pentru toate obiectele
        self.parametri = parametri if parametri is not None else {}
        self.data = data if data is not None else datetime.now()

    def lista_parametri(self):
        # [(nume_parametru, valoare)], valoarea e None daca parametrul nu e setat (ex: ?a)
        rezultat = []
        for nume, valori in self.parametri.items():
            # pastram doar valorile care nu sunt goale (?a si ?a= dau o valoare goala)
            valori_setate = []
            for valoare in valori:
                if valoare != '':
                    valori_setate.append(valoare)

            if not valori_setate:
                rezultat.append((nume, None))
            elif len(valori_setate) == 1:
                rezultat.append((nume, valori_setate[0]))
            else:
                rezultat.append((nume, valori_setate))
        return rezultat

    def string_url(self):
        return self.url

    def pagina(self):
        return urlparse(self.url).path

    def data_text(self, format=FORMAT_ZI, ce_afisam=''):
        # doar textul datii: ce_afisam='zi' -> doar data, ce_afisam='timp' -> doar ora, altfel data si ora
        if ce_afisam == 'zi':
            return formateaza_data(self.data, format)
        if ce_afisam == 'timp':
            return formateaza_data(self.data, FORMAT_TIMP)
        return formateaza_data(self.data, format + ' ' + FORMAT_TIMP)

    def calculeaza_data(self, format=FORMAT_ZI, ce_afisam=''):
        # sectiunea html "Data si ora", adaugata in pagina /info
        return f"<section><h2>Data și ora</h2><p>{self.data_text(format, ce_afisam)}</p></section>"

    def __str__(self):
        return (f"id: {self.id}\n"
                f"ip_client: {self.ip_client}\n"
                f"string_url: {self.string_url()}\n"
                f"pagina: {self.pagina()}\n"
                f"calculeaza_data: {self.calculeaza_data()}\n"
                f"lista_parametri: {self.lista_parametri()}\n")


# Paginile site-ului

DESCRIERE = (
    "Buchetul este o florărie online care vinde buchete, aranjamente florale și flori la ghiveci. "
    "Clienții pot căuta și sorta florile după categorie, ocazie, preț sau culoare, pot vedea detaliile "
    "fiecărui produs și pot plasa o comandă simplă, cu livrare în București."
)


def index(request):
    return HttpResponse(f"<p>{DESCRIERE}</p>")


def info(request):
    # /info?data=zi -> doar data, /info?data=timp -> doar ora
    ce_afisam = request.GET.get('data', '')
    return HttpResponse(f"""<!DOCTYPE html>
<html lang="ro">
<head>
    <meta charset="utf-8">
    <title>Informații despre server</title>
</head>
<body>
    <h1>Informații despre server</h1>
    {request.accesare.calculeaza_data(ce_afisam=ce_afisam)}
</body>
</html>""")
