
from django import forms

from .models import DrawDown


class DrawDownForm(forms.ModelForm):

    class Meta:
        model = DrawDown
        fields = ('agreement_id', 'reference', 'amount', 'agreement_type', 'agreement_phase')
