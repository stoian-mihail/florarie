from collections import Counter
from datetime import datetime
from urllib.parse import urlparse

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, F, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import AdaugaInCosForm, ComandaForm, ContactForm, FiltruProduseForm
from .models import Comanda, Floare, LinieComanda, Ocazie


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


# ---------------------------------------------------------------------------
# Magazinul: produse, cos virtual, comanda
# ---------------------------------------------------------------------------

PRODUSE_PE_PAGINA = 6


def produse(request):
    # filtrare, cautare si sortare dupa parametrii din URL (formular trimis prin GET)
    form = FiltruProduseForm(request.GET)
    flori = Floare.objects.select_related('categorie')

    if form.is_valid():
        date = form.cleaned_data
        if date['q']:
            flori = flori.filter(Q(nume__icontains=date['q']) | Q(descriere__icontains=date['q']))
        if date['categorie']:
            flori = flori.filter(categorie=date['categorie'])
        if date['ocazie']:
            flori = flori.filter(ocazii=date['ocazie'])
        if date['tip']:
            flori = flori.filter(tip=date['tip'])
        if date['pret_min'] is not None:
            flori = flori.filter(pret__gte=date['pret_min'])
        if date['pret_max'] is not None:
            flori = flori.filter(pret__lte=date['pret_max'])
        if date['doar_in_stoc']:
            flori = flori.filter(stoc__gt=0)
        if date['sortare']:
            flori = flori.order_by(date['sortare'])

    # paginare
    paginator = Paginator(flori, PRODUSE_PE_PAGINA)
    pagina = paginator.get_page(request.GET.get('pagina'))

    # parametrii filtrelor, fara "pagina", ca sa ii pastram in linkurile de paginare
    parametri = request.GET.copy()
    parametri.pop('pagina', None)

    return render(request, 'florarie/produse.html', {
        'form': form,
        'pagina': pagina,
        'parametri': parametri.urlencode(),
    })


def produs(request, slug):
    floare = get_object_or_404(Floare.objects.select_related('categorie', 'furnizor', 'ambalaj'), slug=slug)
    return render(request, 'florarie/produs.html', {
        'floare': floare,
        'form': AdaugaInCosForm(),
    })


# cosul e tinut in sesiune, ca dictionar {id_floare (string): cantitate}

def citeste_cos(request):
    return request.session.get('cos', {})


def salveaza_cos(request, cos):
    request.session['cos'] = cos


def continut_cos(cos):
    # lista de (floare, cantitate, subtotal) si totalul cosului
    flori = Floare.objects.in_bulk([int(id_floare) for id_floare in cos])
    linii = []
    for id_floare, cantitate in cos.items():
        floare = flori.get(int(id_floare))
        if floare:
            linii.append((floare, cantitate, floare.pret * cantitate))
    total = sum(subtotal for _, _, subtotal in linii)
    return linii, total


@require_POST
def adauga_in_cos(request, id):
    floare = get_object_or_404(Floare, id=id)
    form = AdaugaInCosForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Cantitatea nu este validă.')
        return redirect('produs', slug=floare.slug)

    cos = citeste_cos(request)
    cantitate = cos.get(str(id), 0) + form.cleaned_data['cantitate']
    if cantitate > floare.stoc:
        messages.error(request, f'Avem doar {floare.stoc} bucăți din „{floare.nume}” în stoc.')
        return redirect('produs', slug=floare.slug)

    cos[str(id)] = cantitate
    salveaza_cos(request, cos)
    messages.success(request, f'„{floare.nume}” a fost adăugat în coș.')
    return redirect('cos_virtual')


@require_POST
def actualizeaza_cos(request):
    cos = citeste_cos(request)
    flori = Floare.objects.in_bulk([int(id_floare) for id_floare in cos])
    for id_floare in list(cos):
        try:
            cantitate = int(request.POST.get(f'cantitate_{id_floare}', cos[id_floare]))
        except ValueError:
            continue
        floare = flori.get(int(id_floare))
        if cantitate <= 0 or floare is None:
            del cos[id_floare]
        else:
            cos[id_floare] = min(cantitate, floare.stoc)
    salveaza_cos(request, cos)
    messages.success(request, 'Coșul a fost actualizat.')
    return redirect('cos_virtual')


@require_POST
def sterge_din_cos(request, id):
    cos = citeste_cos(request)
    cos.pop(str(id), None)
    salveaza_cos(request, cos)
    return redirect('cos_virtual')


def cos_virtual(request):
    linii, total = continut_cos(citeste_cos(request))
    form = ComandaForm(request.POST or None)

    if request.method == 'POST' and linii and form.is_valid():
        try:
            comanda = plaseaza_comanda(form, linii)
        except ValueError as eroare:
            messages.error(request, str(eroare))
            return redirect('cos_virtual')
        salveaza_cos(request, {})
        request.session['ultima_comanda'] = comanda.id
        return redirect('confirmare_comanda', id=comanda.id)

    return render(request, 'florarie/cos_virtual.html', {
        'linii': linii,
        'total': total,
        'form': form,
        'livrare_gratuita': bool(linii) and total >= settings.DATE_FIRMA['livrare_gratuita_de_la'],
    })


def plaseaza_comanda(form, linii):
    # totul intr-o tranzactie: daca un produs nu mai e in stoc, nu se salveaza nimic
    with transaction.atomic():
        ids = [floare.id for floare, _, _ in linii]
        stocuri = Floare.objects.select_for_update().in_bulk(ids)
        for floare, cantitate, _ in linii:
            if stocuri[floare.id].stoc < cantitate:
                raise ValueError(f'Stoc insuficient pentru „{floare.nume}” '
                                 f'(mai sunt {stocuri[floare.id].stoc} bucăți).')
        comanda = form.save()
        for floare, cantitate, _ in linii:
            LinieComanda.objects.create(comanda=comanda, floare=floare,
                                        cantitate=cantitate, pret_unitar=floare.pret)
            Floare.objects.filter(id=floare.id).update(stoc=F('stoc') - cantitate)
    return comanda


def confirmare_comanda(request, id):
    # doar cel care a plasat comanda o poate vedea
    if request.session.get('ultima_comanda') != id:
        raise Http404('Comanda nu a fost găsită.')
    comanda = get_object_or_404(Comanda.objects.prefetch_related('linii__floare'), id=id)
    return render(request, 'florarie/confirmare_comanda.html', {'comanda': comanda})


# ---------------------------------------------------------------------------
# Ocazii, livrare, contact
# ---------------------------------------------------------------------------

def ocazii(request):
    return render(request, 'florarie/ocazii.html', {
        'ocazii': Ocazie.objects.annotate(nr_flori=Count('flori')).order_by('nume'),
    })


def livrare(request):
    return render(request, 'florarie/livrare.html')


def contact(request):
    form = ContactForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        date = form.cleaned_data
        # in dezvoltare, e-mailul este afisat in consola serverului
        send_mail(
            subject=f'[Contact] {date["subiect"]}',
            message=f'De la: {date["nume"]} <{date["email"]}>\n\n{date["mesaj"]}',
            from_email=date['email'],
            recipient_list=['contact@florariapetale.ro'],
        )
        messages.success(request, 'Mesajul a fost trimis. Vă răspundem în cel mult o zi lucrătoare.')
        return redirect('contact')
    return render(request, 'florarie/contact.html', {'form': form})
