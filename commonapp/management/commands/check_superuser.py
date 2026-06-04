from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Check if there is any superuser'

    def handle(self, *args, **kwargs):
        User = get_user_model()
        if not User.objects.filter(is_superuser=True).exists():
            self.stdout.write(self.style.SUCCESS('Superuser does not exist, creating superuser'))
            User.objects.create_superuser(username='admin', email='admin@example.com', password='admin@123')
            self.stdout.write(self.style.SUCCESS('Superuser created successfully'))
        else:
            self.stdout.write(self.style.SUCCESS('Superuser already exists'))
            