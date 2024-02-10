import csv
import datetime
import hashlib
import os

import requests
from bs4 import BeautifulSoup
import logging

from django.db import transaction

from phone.models import Operator

requests.packages.urllib3.disable_warnings()
CSV_DATA_PATH = "phone/data"
BATCH_SIZE = 512


def generate_hash(row: map) -> str:
    """Генерация хеша строки для последующего быстрого сравнения"""

    row_str = ":".join(row)
    return hashlib.md5(row_str.encode('utf8')).hexdigest()


def process_csv_file(filename: str):
    """Прочтение скачанных данных из csv-файлов.
    Используем хеш для того чтобы быстро пропустить не обновленные строки.
    Используем пакетное обновление (bulk_update) для оптимизации.
    Предполагаю, что диапазон номеров с кодом остаются неимзенными,
        и меняться могут только операторы и их ИНН. Разбиваться на более мелкие
        диапазоны они не станут.
    Также предполагается что в таблице нет дубликатов, я не стал делать проверку и их удаление.
    Возможно использование двух хешей немного излишне.
    """

    logging.info(f"write {filename}...")
    full_path = os.path.join(CSV_DATA_PATH, filename)
    start_time = datetime.datetime.now()
    full_updated_operators = 0
    full_created_operators = 0
    operators_to_create = []
    operators_to_update = []

    with open(full_path, 'r', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        create_batch_number: int = 1
        update_batch_number: int = 1
        row: dict

        for row in reader:
            hash_id = generate_hash(map(str, [row['АВС/ DEF'], row['От'], row['До']]))
            hash_row = generate_hash(map(str, row.values()))
            operator_data = {
                'code': row['АВС/ DEF'],
                'range_start': row['От'],
                'range_end': row['До'],
                'capacity': row['Емкость'],
                'name': row['Оператор'],
                'region': row['Регион'],
                'operator_inn': row['ИНН'],
                'hash_id': hash_id,
                'hash_row': hash_row
            }

            try:
                # Поиск по хешу идентификатора
                operator = Operator.objects.get(hash_id=hash_id)
                if operator.hash_row == hash_row:
                    # Если хеш строки тот-же - пропускаем
                    continue
                # В ином случае - вносим новые данные, и добавляем к обновляемым
                for key, value in operator_data.items():
                    setattr(operator, key, value)
                operators_to_update.append(operator)

            # Если оператор не был найден по хешу идентификатора - значит не существует
            except Operator.DoesNotExist:
                operators_to_create.append(Operator(**operator_data))

            # Проверяем, достигли ли мы размера пакета для пакетного создания/обновления
            if len(operators_to_create) >= BATCH_SIZE:
                logging.info(f"\t#{create_batch_number} create batch size: {len(operators_to_create)}, "
                             f"sum: {full_created_operators}")
                Operator.objects.bulk_create(operators_to_create, ignore_conflicts=True)
                full_created_operators += len(operators_to_create)
                create_batch_number += 1
                operators_to_create = []

            if len(operators_to_update) >= BATCH_SIZE:
                logging.info(f"\t#{update_batch_number} update batch size: {len(operators_to_update)}, "
                             f"sum: {full_updated_operators}")
                Operator.objects.bulk_update(operators_to_update, ['name', 'region', 'operator_inn', 'hash_row'])
                full_updated_operators += len(operators_to_update)
                update_batch_number += 1
                operators_to_update = []

        # Обрабатываем оставшиеся записи после завершения цикла
        with transaction.atomic():
            if operators_to_create:
                logging.info(f"\tfinal create batch size: {len(operators_to_create)}")
                full_created_operators += len(operators_to_create)
                Operator.objects.bulk_create(operators_to_create, ignore_conflicts=True)

            if operators_to_update:
                logging.info(f"\tfinal update batch size: {len(operators_to_update)}")
                full_updated_operators += len(operators_to_update)
                Operator.objects.bulk_update(operators_to_update, ['name', 'region', 'operator_inn', 'hash_row'])

        logging.info(f"file {filename} updating {datetime.datetime.now() - start_time}\n"
                     f"\tupdated operators: {full_updated_operators}\n"
                     f"\tcreated operators: {full_created_operators}")


def process_csv_files():
    logging.info("all files downloaded, start processing write operators...")
    for filename in os.listdir(CSV_DATA_PATH):
        if filename.endswith(".csv"):
            process_csv_file(filename)


def download_csv_files():
    """Загрузка файлов с сайта.
    Тут перед сохранением можно проверить хеш файлов,
        выяснить, изменилось ли их содержимое таблиц в течение дня.
    Но я не сделал. Но можно.
    """

    # Получение данных страницы
    logging.info("start updating operators...")
    url: str = "https://opendata.digital.gov.ru/registry/numeric/downloads"
    response = requests.get(url, verify=False)  # verify=False небезопасен, это быстрое решение
    if response.status_code != 200:
        logging.error(f"parse phone number site error: {response.status_code}")
        return

    # Парсинг страницы на поиск ссылок
    soup = BeautifulSoup(response.text, 'html.parser')
    links = soup.find_all('a', href=True)
    csv_links = [link['href'] for link in links if 'csv' in link['href']]

    # Создаем каталог, если он не существует
    directory = CSV_DATA_PATH
    if not os.path.exists(directory):
        os.makedirs(directory)

    for link in csv_links:
        file_name = CSV_DATA_PATH + link.split('/')[-1].split('?')[0]
        answer = requests.get(link, verify=False)
        if answer.status_code == 200:
            with open(file_name, 'wb') as f:
                f.write(answer.content)
            logging.info(f"file {file_name} has downloaded")
        else:
            logging.error(f"download csv error {file_name}: {answer.status_code}")


def get_operator_info(phone: str):
    """ Возвращает информацию об операторе и регионе для заданного номера телефона

    Args:
        phone(str): Номер телефона в формате "79000000000"
    """

    # Убираем первую цифру, забираем код номера
    try:
        phone_code = int(phone[1:4])
        phone_number = int(phone[4:])
    except ValueError:
        return None

    # Используем фильтрацию модели для поиска оператора, чей диапазон включает данный номер
    try:
        operator = Operator.objects.get(code=phone_code, range_start__lte=phone_number, range_end__gte=phone_number)
        return {
            "phone": phone,
            "name": operator.name,
            "region": operator.region,
        }

    except Operator.DoesNotExist:
        return None
