from django import forms

from .models import Categorie, Comanda, Floare, Ocazie


class StilBootstrap:
    # adauga clasele Bootstrap 4 pe toate campurile formularului
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for camp in self.fields.values():
            if isinstance(camp.widget, forms.CheckboxInput):
                camp.widget.attrs['class'] = 'form-check-input'
            else:
                camp.widget.attrs['class'] = 'form-control'


class FiltruProduseForm(StilBootstrap, forms.Form):
    # formular trimis prin GET: filtrele raman in URL (se pot copia / pagina)
    SORTARI = [
        ('nume', 'Nume (A-Z)'),
        ('-nume', 'Nume (Z-A)'),
        ('pret', 'Preț crescător'),
        ('-pret', 'Preț descrescător'),
        ('-data_adaugare', 'Cele mai noi'),
    ]

    q = forms.CharField(label='Caută', required=False)
    categorie = forms.ModelChoiceField(Categorie.objects.all(), required=False, empty_label='Toate')
    ocazie = forms.ModelChoiceField(Ocazie.objects.all(), required=False, empty_label='Toate')
    tip = forms.ChoiceField(choices=[('', 'Toate')] + Floare.Tip.choices, required=False)
    pret_min = forms.DecimalField(label='Preț minim', required=False, min_value=0)
    pret_max = forms.DecimalField(label='Preț maxim', required=False, min_value=0)
    doar_in_stoc = forms.BooleanField(label='Doar în stoc', required=False)
    sortare = forms.ChoiceField(choices=SORTARI, required=False)

    def clean(self):
        date = super().clean()
        pret_min, pret_max = date.get('pret_min'), date.get('pret_max')
        if pret_min is not None and pret_max is not None and pret_min > pret_max:
            raise forms.ValidationError('Prețul minim nu poate fi mai mare decât prețul maxim.')
        return date


class AdaugaInCosForm(forms.Form):
    cantitate = forms.IntegerField(min_value=1, max_value=50, initial=1)


class ComandaForm(StilBootstrap, forms.ModelForm):
    class Meta:
        model = Comanda
        fields = ['nume_client', 'email', 'telefon', 'adresa_livrare', 'observatii']
        labels = {
            'nume_client': 'Nume și prenume',
            'email': 'E-mail',
            'adresa_livrare': 'Adresa de livrare',
            'observatii': 'Observații (opțional)',
        }
        widgets = {'observatii': forms.Textarea(attrs={'rows': 3})}


class ContactForm(StilBootstrap, forms.Form):
    nume = forms.CharField(max_length=100)
    email = forms.EmailField(label='E-mail')
    subiect = forms.CharField(max_length=100)
    mesaj = forms.CharField(widget=forms.Textarea(attrs={'rows': 5}), min_length=10)
