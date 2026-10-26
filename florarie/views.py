from collections import Counter
from datetime import datetime
from urllib.parse import urlparse

from django.http import Http404
from django.shortcuts import render
from django.urls import reverse


# ---------------------------------------------------------------------------
# Lab 1: data in limba romana
# ---------------------------------------------------------------------------

ZILE = ['Luni', 'Marți', 'Miercuri', 'Joi', 'Vineri', 'Sâmbătă', 'Duminică']
LUNI = ['Ianuarie', 'Februarie', 'Martie', 'Aprilie', 'Mai', 'Iunie',
        'Iulie', 'August', 'Septembrie', 'Octombrie', 'Noiembrie', 'Decembrie']

# formatul cerut: [zi din saptamana], [zi din luna] [numele lunii] [an] -> Joi, 2 Octombrie 2025
FORMAT_ZI = '%A, %-d %B %Y'
FORMAT_TIMP = '%H:%M:%S'


def formateaza_data(data, format=FORMAT_ZI):
    # functie comuna, folosita si de /info si de clasa Accesare (ca sa nu avem codul in 2 locuri)
    # %A, %B si %-d sunt inlocuite de noi in romana, restul formatului il trateaza strftime
    format = (format.replace('%A', ZILE[data.weekday()])
                    .replace('%B', LUNI[data.month - 1])
                    .replace('%-d', str(data.day)))
    return data.strftime(format)


# ---------------------------------------------------------------------------
# Lab 1: clasa Accesare
# ---------------------------------------------------------------------------

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
            valori = [v for v in valori if v != '']
            if not valori:
                rezultat.append((nume, None))
            elif len(valori) == 1:
                rezultat.append((nume, valori[0]))
            else:
                rezultat.append((nume, valori))
        return rezultat

    def string_url(self):
        return self.url

    def pagina(self):
        return urlparse(self.url).path

    def calculeaza_data(self, format=FORMAT_ZI, tip=''):
        # tip='zi' -> doar data, tip='timp' -> doar ora, altfel data si ora
        if tip == 'zi':
            return formateaza_data(self.data, format)
        if tip == 'timp':
            return formateaza_data(self.data, FORMAT_TIMP)
        return formateaza_data(self.data, format + ' ' + FORMAT_TIMP)

    def __str__(self):
        return (f"id: {self.id}\n"
                f"ip_client: {self.ip_client}\n"
                f"string_url: {self.string_url()}\n"
                f"pagina: {self.pagina()}\n"
                f"calculeaza_data: {self.calculeaza_data()}\n"
                f"lista_parametri: {self.lista_parametri()}\n")


# toate accesarile din sesiunea curenta a serverului (se pierd la repornire)
ACCESARI = []


# ---------------------------------------------------------------------------
# Paginile site-ului
# ---------------------------------------------------------------------------

def index(request):
    return render(request, 'florarie/index.html')


def despre(request):
    return render(request, 'florarie/despre.html')


def istoric(request):
    return render(request, 'florarie/istoric.html')


def in_lucru(request):
    # paginile din meniu care nu sunt inca implementate
    return render(request, 'florarie/in_lucru.html')


def info(request):
    # Lab 1: /info?data=zi -> doar data, /info?data=timp -> doar ora
    tip = request.GET.get('data', '')
    return render(request, 'florarie/info.html', {
        'data_server': request.accesare.calculeaza_data(tip=tip),
    })


# ---------------------------------------------------------------------------
# Lab 2: /log
# ---------------------------------------------------------------------------

PROPRIETATI = ['id', 'ip_client', 'url', 'parametri', 'data']

# numele (din urls.py) paginilor luate in calcul la "cea mai/putin accesata pagina"
PAGINI_SITE = ['index', 'info', 'log', 'despre', 'istoric', 'produse',
               'contact', 'cos_virtual', 'ocazii', 'livrare']


def valoare_proprietate(accesare, nume):
    if nume == 'data':
        return accesare.calculeaza_data()
    if nume == 'parametri':
        return accesare.lista_parametri()
    return getattr(accesare, nume)


def log(request):
    erori = []
    eroare_finala = None
    accesari = ACCESARI

    # /log?iduri=2,3&iduri=5&iduri=4,2,1[&dubluri=true]
    if 'iduri' in request.GET:
        dubluri = request.GET.get('dubluri', 'false') == 'true'
        iduri = []
        for valoare in request.GET.getlist('iduri'):
            for bucata in valoare.split(','):
                bucata = bucata.strip()
                if not bucata.isdigit():
                    erori.append(f"Id invalid: '{bucata}'")
                    continue
                id_cerut = int(bucata)
                if dubluri or id_cerut not in iduri:
                    iduri.append(id_cerut)
        dupa_id = {a.id: a for a in ACCESARI}
        accesari = [dupa_id[i] for i in iduri if i in dupa_id]

    # /log?ultimele=n
    elif 'ultimele' in request.GET:
        try:
            n = int(request.GET['ultimele'])
        except ValueError:
            n = None
            erori.append("Parametrul ultimele trebuie să fie un număr întreg.")
        if n is not None:
            if n < 0:
                erori.append("Parametrul ultimele nu poate fi negativ.")
            elif n > len(ACCESARI):
                eroare_finala = f"Exista doar {len(ACCESARI)} accesari fata de {n} accesari cerute"
            else:
                accesari = ACCESARI[len(ACCESARI) - n:]

    # /log?tabel=tot sau /log?tabel=id,url
    coloane = None
    randuri = []
    if 'tabel' in request.GET:
        tabel = request.GET['tabel']
        if tabel == 'tot':
            coloane = PROPRIETATI
        else:
            coloane = [c.strip() for c in tabel.split(',') if c.strip()]
            for c in coloane:
                if c not in PROPRIETATI:
                    erori.append(f"Proprietate necunoscută: '{c}'")
            coloane = [c for c in coloane if c in PROPRIETATI]
        randuri = [[valoare_proprietate(a, c) for c in coloane] for a in accesari]

    # cea mai putin / cea mai mult accesata pagina (paginile neaccesate au 0)
    contor = Counter(a.pagina() for a in ACCESARI)
    for nume in PAGINI_SITE:
        contor.update({reverse(nume): 0})
    cea_mai_accesata = max(contor, key=contor.get)
    cea_mai_putin_accesata = min(contor, key=contor.get)

    return render(request, 'florarie/log.html', {
        'accesari': accesari,
        'coloane': coloane,
        'randuri': randuri,
        'erori': erori,
        'eroare_finala': eroare_finala,
        'accesari_param': request.GET.get('accesari'),  # 'nr' sau 'detalii'
        'numar_accesari': len(ACCESARI),
        'parametri_primiti': list(request.GET.keys()),
        'cea_mai_accesata': (cea_mai_accesata, contor[cea_mai_accesata]),
        'cea_mai_putin_accesata': (cea_mai_putin_accesata, contor[cea_mai_putin_accesata]),
    })


def accesare_detaliu(request, id):
    # Lab 2: ruta /accesare[id] definita cu re_path
    for accesare in ACCESARI:
        if accesare.id == int(id):
            return render(request, 'florarie/accesare.html', {'accesare': accesare})
    raise Http404(f"Nu există accesarea cu id-ul {id}")
