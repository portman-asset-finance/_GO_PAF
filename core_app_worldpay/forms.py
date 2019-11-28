from django import forms
from .models import Collection_WorldPay

class collection_agreementForm(forms.ModelForm):
    class Meta:
        model = Collection_WorldPay
        fields = ('collection_number', 'agreement_number', 'collection_quantity', 'created_on','user_name', )