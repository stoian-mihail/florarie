from django.urls import path, re_path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('info', views.info, name='info'),
    path('log', views.log, name='log'),
    path('despre', views.despre, name='despre'),
    path('istoric', views.istoric, name='istoric'),
    # Lab 4: magazinul
    path('produse', views.produse, name='produse'),
    path('produse/<slug:slug>', views.produs, name='produs'),
    # pagini inca neimplementate -> template-ul in_lucru.html
    path('contact', views.in_lucru, name='contact'),
    path('cos_virtual', views.in_lucru, name='cos_virtual'),
    path('ocazii', views.in_lucru, name='ocazii'),
    path('livrare', views.in_lucru, name='livrare'),
    # Lab 2: /accesare[id], de exemplu /accesare7
    re_path(r'^accesare(?P<id>[0-9]+)$', views.accesare_detaliu, name='accesare'),
]
