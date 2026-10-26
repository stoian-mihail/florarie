from django.contrib.auth.hashers import make_password
from django.db import migrations


def creeaza_admin(apps, schema_editor):
    # contul de administrare se creeaza automat la "python manage.py migrate"
    # (doar pentru dezvoltare: utilizator admin, parola password)
    User = apps.get_model('auth', 'User')
    if not User.objects.filter(username='admin').exists():
        User.objects.create(
            username='admin',
            email='admin@buchetul.ro',
            password=make_password('password'),
            is_staff=True,
            is_superuser=True,
        )


def sterge_admin(apps, schema_editor):
    apps.get_model('auth', 'User').objects.filter(username='admin').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('florarie', '0002_comanda_liniecomanda'),
    ]

    operations = [
        migrations.RunPython(creeaza_admin, sterge_admin),
    ]
