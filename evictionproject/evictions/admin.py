from django.contrib import admin

from .models import Case, Court

admin.site.index_template = "admin/index.html"
admin.site.register(Court)

class CaseAdmin(admin.ModelAdmin):
    list_display = ['ujs_id', 'court', 'status', 'defendant', 'plaintiff']
    list_filter = ['court', 'defendant_zipcode', 'plaintiff_zipcode']
    search_fields = ['court__id', 'defendant', 'plaintiff']

admin.site.register(Case, CaseAdmin)
