from django.urls import path, re_path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('info', views.info, name='info'),
    path('log', views.log, name='log'),
    path('despre', views.despre, name='despre'),
    path('istoric', views.istoric, name='istoric'),
    path('ocazii', views.ocazii, name='ocazii'),
    path('livrare', views.livrare, name='livrare'),
    path('contact', views.contact, name='contact'),
    # magazinul
    path('produse', views.produse, name='produse'),
    path('produse/<slug:slug>', views.produs, name='produs'),
    path('cos_virtual', views.cos_virtual, name='cos_virtual'),
    path('cos/adauga/<int:id>', views.adauga_in_cos, name='adauga_in_cos'),
    path('cos/actualizeaza', views.actualizeaza_cos, name='actualizeaza_cos'),
    path('cos/sterge/<int:id>', views.sterge_din_cos, name='sterge_din_cos'),
    path('comanda/<int:id>', views.confirmare_comanda, name='confirmare_comanda'),
    # pagina pentru sectiunile neterminate (Lab 2); momentan nu mai e folosita in meniu
    path('in_lucru', views.in_lucru, name='in_lucru'),
    # Lab 2: /accesare[id], de exemplu /accesare7
    re_path(r'^accesare(?P<id>[0-9]+)$', views.accesare_detaliu, name='accesare'),
]
