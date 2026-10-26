from django.contrib import admin

from .models import (Ambalaj, Categorie, Comanda, Floare, Florarie, Furnizor, LinieComanda,
                     Ocazie, Raion)


@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ('nume', 'sezon', 'culoare', 'sigla')
    list_filter = ('sezon',)
    search_fields = ('nume',)


@admin.register(Furnizor)
class FurnizorAdmin(admin.ModelAdmin):
    list_display = ('nume', 'email', 'telefon', 'tara', 'partener_din')
    list_filter = ('tara',)
    search_fields = ('nume', 'email')


@admin.register(Ambalaj)
class AmbalajAdmin(admin.ModelAdmin):
    list_display = ('nume', 'material', 'pret', 'reciclabil')
    list_filter = ('material', 'reciclabil')


@admin.register(Ocazie)
class OcazieAdmin(admin.ModelAdmin):
    list_display = ('nume', 'data_start', 'data_sfarsit')
    search_fields = ('nume',)


@admin.register(Floare)
class FloareAdmin(admin.ModelAdmin):
    list_display = ('nume', 'categorie', 'tip', 'pret', 'stoc', 'parfumata', 'data_adaugare')
    list_filter = ('categorie', 'tip', 'parfumata', 'ocazii')
    search_fields = ('nume', 'descriere')
    prepopulated_fields = {'slug': ('nume',)}
    filter_horizontal = ('ocazii',)


class RaionInline(admin.TabularInline):
    # raioanele se editeaza direct din pagina florariei (entitate slaba)
    model = Raion
    extra = 1


@admin.register(Florarie)
class FlorarieAdmin(admin.ModelAdmin):
    list_display = ('nume', 'oras', 'adresa', 'telefon', 'deschisa_duminica')
    list_filter = ('oras', 'deschisa_duminica')
    inlines = [RaionInline]


@admin.register(Raion)
class RaionAdmin(admin.ModelAdmin):
    list_display = ('florarie', 'numar', 'nume', 'temperatura', 'suprafata_mp')
    list_filter = ('florarie',)


class LinieComandaInline(admin.TabularInline):
    model = LinieComanda
    extra = 0


@admin.register(Comanda)
class ComandaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nume_client', 'telefon', 'stare', 'data_plasare', 'total')
    list_filter = ('stare',)
    search_fields = ('nume_client', 'email', 'telefon')
    list_editable = ('stare',)
    inlines = [LinieComandaInline]
