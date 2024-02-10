import logging

from django.core.management import BaseCommand

from phone.tasks import update_operators_data


class Command(BaseCommand):
    """Команда для выполнения обновления операторов без ожидания процесса в celery"""

    help = """Обновить список операторов"""

    def handle(self, *args, **options):
        update_operators_data()
