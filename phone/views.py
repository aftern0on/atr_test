from typing import Optional, Union

from django.shortcuts import render
from pydantic import ValidationError
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from phone import dto
from phone.tasks import update_operators_data
from phone.utils import get_operator_info


@api_view(["POST"])
def update_operators(request: Request):
    """Обновление пользователей.
    Сделал отдельно в виде эндпоинта, никакой защиты тут нет, но сделать-то можно.
    """

    update_operators_data()
    return Response(status=status.HTTP_200_OK, data={'description': 'ok'})


@api_view(["GET", "POST"])
def check_phone_form(request):
    """Выдача шаблонизированной формы для получения данных о введенном телефоне"""

    operator_info: Union[dict, bool, None]
    if request.method == "POST":
        phone_number = request.POST.get('phone')
        operator_info = get_operator_info(phone_number)
    else:
        operator_info = False

    return render(request, 'check_phone.html', {"operator_info": operator_info})


@api_view(["POST"])
def check_phone(request: Request):
    """Получение информации о введенном телефоне
    Пример запроса в JSON:
        {
            "phone": "79000000000"
        }
    """

    # Вообще лучше реализовывать разделение бизнес-логики от представлений
    # Однако проект сам по себе не такой сложный, по этому обработку можно делать как угодно, я думаю
    try:
        data = dto.Phone(**request.data)
    except ValidationError:
        return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": "phone number error"})

    result = get_operator_info(data.phone)
    if result:
        return Response(status=status.HTTP_200_OK, data=result)
    else:
        return Response(status=status.HTTP_400_BAD_REQUEST, data={"error": "number not found"})


