from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import F, Q


class Categorie(models.Model):
    class Sezon(models.TextChoices):
        PRIMAVARA = 'primavara', 'Primăvară'
        VARA = 'vara', 'Vară'
        TOAMNA = 'toamna', 'Toamnă'
        IARNA = 'iarna', 'Iarnă'
        TOT_ANUL = 'tot_anul', 'Tot anul'

    nume = models.CharField(
        max_length=50,
        unique=True,
        error_messages={'unique': 'Există deja o categorie cu acest nume.'},
    )
    descriere = models.TextField()
    culoare = models.CharField(
        max_length=7,
        default='#3d6b47',
        help_text='Cod hex al culorii folosite la stilizarea categoriei, de exemplu #c2537a.',
    )
    sigla = models.CharField(
        max_length=50,
        help_text='Numele unei iconițe FontAwesome, de exemplu fa-seedling.',
    )
    sezon = models.CharField(max_length=10, choices=Sezon.choices, default=Sezon.TOT_ANUL)

    class Meta:
        verbose_name = 'categorie'
        verbose_name_plural = 'categorii'
        ordering = ['nume']

    def __str__(self):
        return self.nume


class Furnizor(models.Model):
    nume = models.CharField(max_length=100)
    email = models.EmailField(
        unique=True,
        error_messages={
            'unique': 'Există deja un furnizor cu această adresă de e-mail.',
            'invalid': 'Adresa de e-mail nu este validă.',
        },
    )
    telefon = models.CharField(max_length=20)
    website = models.URLField(null=True, blank=True)
    tara = models.CharField(max_length=50, default='România')
    partener_din = models.DateField(help_text='Data de la care colaborăm cu furnizorul.')

    class Meta:
        verbose_name = 'furnizor'
        verbose_name_plural = 'furnizori'
        indexes = [
            models.Index(fields=['nume'], name='furnizor_nume_idx'),
        ]

    def __str__(self):
        return self.nume


class Ambalaj(models.Model):
    class Material(models.TextChoices):
        HARTIE = 'hartie', 'Hârtie'
        CELOFAN = 'celofan', 'Celofan'
        CUTIE = 'cutie', 'Cutie'
        COS = 'cos', 'Coș'

    nume = models.CharField(
        max_length=30,
        unique=True,
        error_messages={'unique': 'Există deja un ambalaj cu acest nume.'},
    )
    material = models.CharField(max_length=10, choices=Material.choices)
    pret = models.DecimalField(max_digits=6, decimal_places=2)
    reciclabil = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'ambalaj'
        verbose_name_plural = 'ambalaje'
        constraints = [
            models.CheckConstraint(
                condition=Q(pret__gte=0),
                name='ambalaj_pret_nenegativ',
                violation_error_message='Prețul ambalajului nu poate fi negativ.',
            ),
        ]

    def __str__(self):
        return self.nume


class Ocazie(models.Model):
    nume = models.CharField(max_length=50, unique=True)
    # default + blank=True: campul poate fi lasat liber in formularul din admin
    descriere = models.TextField(default='', blank=True)
    data_start = models.DateField(null=True, blank=True)
    data_sfarsit = models.DateField(
        null=True,
        blank=True,
        help_text='Lăsați liber dacă ocazia nu are o perioadă fixă (de exemplu, aniversările).',
    )

    class Meta:
        verbose_name = 'ocazie'
        verbose_name_plural = 'ocazii'
        constraints = [
            # perioada ocaziei: sfarsitul nu poate fi inaintea inceputului
            models.CheckConstraint(
                condition=Q(data_start__isnull=True) | Q(data_sfarsit__isnull=True)
                | Q(data_sfarsit__gte=F('data_start')),
                name='ocazie_perioada_corecta',
                violation_error_message='Data de sfârșit nu poate fi înaintea datei de început.',
            ),
        ]

    def __str__(self):
        return self.nume


class Floare(models.Model):
    class Tip(models.TextChoices):
        BUCHET = 'buchet', 'Buchet'
        GHIVECI = 'ghiveci', 'Floare la ghiveci'
        ARANJAMENT = 'aranjament', 'Aranjament floral'
        FIR = 'fir', 'Fir individual'

    nume = models.CharField(
        max_length=60,
        unique=True,
        error_messages={
            'unique': 'Există deja o floare cu acest nume.',
            'max_length': 'Numele poate avea cel mult 60 de caractere.',
        },
    )
    slug = models.SlugField(
        max_length=70,
        unique=True,
        help_text='Partea din adresa paginii produsului, de exemplu trandafiri-rosii.',
        error_messages={'unique': 'Slug-ul trebuie să fie unic.'},
    )
    descriere = models.TextField(null=True, blank=True)
    pret = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        error_messages={'max_digits': 'Prețul poate avea cel mult 6 cifre înainte de virgulă.'},
    )
    stoc = models.PositiveIntegerField(default=0)
    inaltime_cm = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Înălțimea aproximativă, în centimetri.',
    )
    tip = models.CharField(max_length=12, choices=Tip.choices, default=Tip.BUCHET)
    parfumata = models.BooleanField(default=False)
    # atributul cu valori multiple (vector de valori) din diagrama
    culori = ArrayField(
        models.CharField(max_length=20),
        default=list,
        blank=True,
        help_text='Culorile florilor, separate prin virgulă (de exemplu: roșu,alb).',
    )
    imagine = models.ImageField(upload_to='flori/', null=True, blank=True)
    data_adaugare = models.DateTimeField(auto_now_add=True)

    categorie = models.ForeignKey(Categorie, on_delete=models.PROTECT, related_name='flori')
    furnizor = models.ForeignKey(Furnizor, on_delete=models.PROTECT, related_name='flori')
    ambalaj = models.ForeignKey(Ambalaj, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='flori')
    ocazii = models.ManyToManyField(Ocazie, blank=True, related_name='flori')

    class Meta:
        verbose_name = 'floare'
        verbose_name_plural = 'flori'
        ordering = ['nume']
        indexes = [
            models.Index(fields=['pret'], name='floare_pret_idx'),
            models.Index(fields=['categorie', 'pret'], name='floare_categorie_pret_idx'),
            models.Index(fields=['-data_adaugare'], name='floare_data_adaugare_idx'),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(pret__gt=0),
                name='floare_pret_pozitiv',
                violation_error_message='Prețul trebuie să fie mai mare decât 0.',
            ),
            models.CheckConstraint(
                condition=Q(inaltime_cm__isnull=True) | Q(inaltime_cm__gte=5, inaltime_cm__lte=300),
                name='floare_inaltime_realista',
                violation_error_message='Înălțimea trebuie să fie între 5 și 300 cm.',
            ),
            # la florile la ghiveci clientii trebuie sa stie cat de mare e planta
            models.CheckConstraint(
                condition=~Q(tip='ghiveci') | Q(inaltime_cm__isnull=False),
                name='floare_ghiveci_cu_inaltime',
                violation_error_message='Pentru florile la ghiveci trebuie completată înălțimea.',
            ),
        ]

    def __str__(self):
        return self.nume


class Florarie(models.Model):
    nume = models.CharField(max_length=60)
    adresa = models.CharField(max_length=150)
    oras = models.CharField(max_length=50)
    telefon = models.CharField(max_length=20)
    deschisa_duminica = models.BooleanField(
        default=False,
        help_text='Bifați dacă sediul are program și duminica.',
    )
    data_deschidere = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = 'florărie'
        verbose_name_plural = 'florării'
        indexes = [
            models.Index(fields=['oras'], name='florarie_oras_idx'),
        ]

    def __str__(self):
        return f'{self.nume} ({self.oras})'


class Raion(models.Model):
    # entitate slaba: un raion exista doar in cadrul unei florarii
    # si e identificat prin (florarie, numar)
    florarie = models.ForeignKey(Florarie, on_delete=models.CASCADE, related_name='raioane')
    numar = models.PositiveSmallIntegerField()
    nume = models.CharField(max_length=50)
    temperatura = models.FloatField(help_text='Temperatura de păstrare a florilor, în °C.')
    suprafata_mp = models.FloatField()

    class Meta:
        verbose_name = 'raion'
        verbose_name_plural = 'raioane'
        ordering = ['florarie', 'numar']
        constraints = [
            models.UniqueConstraint(fields=['florarie', 'numar'], name='raion_unic_in_florarie'),
            models.CheckConstraint(
                condition=Q(temperatura__gte=0, temperatura__lte=30),
                name='raion_temperatura_0_30',
                violation_error_message='Temperatura raionului trebuie să fie între 0 și 30 °C.',
            ),
            models.CheckConstraint(
                condition=Q(suprafata_mp__gt=0),
                name='raion_suprafata_pozitiva',
                violation_error_message='Suprafața trebuie să fie pozitivă.',
            ),
        ]

    def __str__(self):
        return f'{self.florarie.nume} - raionul {self.numar} ({self.nume})'
