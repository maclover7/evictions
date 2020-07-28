from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse

from .forms import CaseImportForm
from .models import Court
from .tasks import get_cases_for_court

def case_import(request):
    if request.method == 'POST':
        form = CaseImportForm(request.POST)
        if form.is_valid():
            courts = form.cleaned_data.get('Courts')
            ujsViewState = form.cleaned_data.get('UJSViewState')
            ujsCaptchaAnswer = form.cleaned_data.get('UJSCaptchaAnswer')
            ujsASPCookie = form.cleaned_data.get('UJSASPCookie')

            for court in courts:
                get_cases_for_court(court, ujsViewState, ujsCaptchaAnswer, ujsASPCookie)

            return HttpResponseRedirect(reverse('admin:index'))
    else:
        form = CaseImportForm

    context = { 'form': form }
    return render(request, 'admin/case_import.html', context)
