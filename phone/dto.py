from pydantic import BaseModel, constr


class Phone(BaseModel):
    """DTO для получения номера телефона"""

    phone: constr(pattern=r'^7\d{10}$')
