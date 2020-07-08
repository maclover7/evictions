import csv
from django.contrib import admin
from django.http import HttpResponse

from .models import Case, Court

admin.site.index_template = "admin/index.html"
admin.site.register(Court)

class ExportCsvMixin:
    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        field_names = [field.name for field in meta.fields]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename={}.csv'.format(meta)
        writer = csv.writer(response)

        writer.writerow(field_names)
        for obj in queryset:
            row = writer.writerow([getattr(obj, field) for field in field_names])

        return response

    export_as_csv.short_description = "Export as CSV"

class CaseAdmin(admin.ModelAdmin, ExportCsvMixin):
    actions = ["export_as_csv"]
    list_display = ['ujs_id', 'court', 'status', 'file_date', 'defendant', 'plaintiff']
    list_filter = ['court', 'defendant_zipcode', 'plaintiff_zipcode']
    search_fields = ['court__id', 'defendant', 'plaintiff']

admin.site.register(Case, CaseAdmin)
