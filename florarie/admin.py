from django.contrib import admin

from .models import Ambalaj, Categorie, Floare, Florarie, Furnizor, Ocazie, Raion


@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ('nume', 'sezon', 'culoare', 'sigla')


@admin.register(Furnizor)
class FurnizorAdmin(admin.ModelAdmin):
    list_display = ('nume', 'email', 'telefon', 'tara', 'partener_din')


@admin.register(Ambalaj)
class AmbalajAdmin(admin.ModelAdmin):
    list_display = ('nume', 'material', 'pret', 'reciclabil')


@admin.register(Ocazie)
class OcazieAdmin(admin.ModelAdmin):
    list_display = ('nume', 'data_start', 'data_sfarsit')


@admin.register(Floare)
class FloareAdmin(admin.ModelAdmin):
    list_display = ('nume', 'categorie', 'tip', 'pret', 'stoc', 'parfumata', 'data_adaugare')
    prepopulated_fields = {'slug': ('nume',)}
    filter_horizontal = ('ocazii',)


class RaionInline(admin.TabularInline):
    # raioanele se editeaza direct din pagina florariei (entitate slaba)
    model = Raion
    extra = 1


@admin.register(Florarie)
class FlorarieAdmin(admin.ModelAdmin):
    list_display = ('nume', 'oras', 'adresa', 'telefon', 'deschisa_duminica')
    inlines = [RaionInline]


@admin.register(Raion)
class RaionAdmin(admin.ModelAdmin):
    list_display = ('florarie', 'numar', 'nume', 'temperatura', 'suprafata_mp')
