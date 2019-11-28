from django import forms
from .models import Notice


class NoticeForm(forms.ModelForm):
    class Meta:
        model = Notice
        fields = ('agreement_number', 'notice_given', 'notice_date', 'secondary_date', )
        widgets = {
            'notice_date': forms.SelectDateWidget(),
            'secondary_date': forms.SelectDateWidget()
        }