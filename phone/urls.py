from django.urls import path
from phone.views import update_operators, check_phone_form, check_phone

urlpatterns = [
    path('update_operators/', update_operators, name='update_operators'),
    path('check_phone/', check_phone, name='check_phone'),
    path('check_phone_form/', check_phone_form, name='check_phone_form')
]