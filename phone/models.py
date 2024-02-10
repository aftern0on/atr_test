from django.db import models


class Operator(models.Model):
    """Хранит данные оператора, облегчает поиск и фильтрацию инфы, можно расширить"""

    name = models.CharField(max_length=512, verbose_name="Оператор")
    region = models.CharField(max_length=512, verbose_name="Регион")
    code = models.CharField(max_length=10, verbose_name="ABC / DEF")
    range_start = models.BigIntegerField(verbose_name="От")
    range_end = models.BigIntegerField(verbose_name="До")
    capacity = models.IntegerField(verbose_name="Емкость")
    operator_inn = models.CharField(max_length=12, verbose_name="ИНН")

    # Хэшированные данные всего объекта
    hash_row = models.CharField(max_length=32, unique=True, db_index=True, verbose_name="Хэш строки")
    # Хэшированные данные которые условно являются уникальными: code:range_start:range_end (предположительно)
    hash_id = models.CharField(max_length=32, unique=True, db_index=True, verbose_name="Хеш идентификатора")

    def __str__(self):
        return f'{self.name} {self.region}'

