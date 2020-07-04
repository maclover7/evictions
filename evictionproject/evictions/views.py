from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse

from .forms import CaseImportForm
from .models import Court
from .tasks import get_new_cases

def case_import(request):
    if request.method == 'POST':
        form = CaseImportForm(request.POST)
        if form.is_valid():
            courts = form.cleaned_data.get('Courts')
            ujsViewState = form.cleaned_data.get('UJSViewState')
            ujsCaptchaAnswer = form.cleaned_data.get('UJSCaptchaAnswer')
            ujsBDocketCookie = form.cleaned_data.get('UJSBDocketCookie')
            ujsASPCookie = form.cleaned_data.get('UJSASPCookie')
            ujsBRootCookie = form.cleaned_data.get('UJSBRootCookie')

            for court in courts:
                get_new_cases(court, ujsViewState, ujsCaptchaAnswer, ujsBDocketCookie, ujsASPCookie, ujsBRootCookie)

            return HttpResponseRedirect(reverse('admin:index'))
    else:
        form = CaseImportForm

    context = { 'form': form }
    return render(request, 'admin/case_import.html', context)
