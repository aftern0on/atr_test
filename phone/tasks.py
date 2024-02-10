import logging

from celery import shared_task

from phone.utils import download_csv_files, process_csv_files


@shared_task
def update_operators_data():
    """Обновляем данные об операторах. Загружаем данные и читаем.
    """

    download_csv_files()
    process_csv_files()
