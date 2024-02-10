from django.contrib import admin
from .models import Operator


class OperatorAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'range_start', 'range_end', 'capacity', 'region', 'operator_inn')
    search_fields = ('name', 'region')
    list_filter = ('region', 'name')
    readonly_fields = ('hash_row', "hash_id")


admin.site.register(Operator, OperatorAdmin)
