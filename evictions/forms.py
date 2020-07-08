from django import forms

from .models import Court

class CaseImportForm(forms.Form):
    def transformForForm(court):
        return [court.id, court.friendly_court_id]

    result = map(transformForForm, Court.objects.all())
    Courts = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple, choices=list(result))
    UJSViewState = forms.CharField()
    UJSCaptchaAnswer = forms.CharField()
    UJSBDocketCookie = forms.CharField()
    UJSASPCookie = forms.CharField()
    UJSBRootCookie = forms.CharField()
