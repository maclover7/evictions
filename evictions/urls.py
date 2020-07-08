from django.urls import path
from django.contrib import admin

from . import views

app_name = 'evictions'

urlpatterns = [
    path('admin/evictions/case_import', admin.site.admin_view(views.case_import), name='case_import'),
]
