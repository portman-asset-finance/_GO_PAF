from django import forms
from .models import Editor


class EditorForm(forms.ModelForm):
    class Meta:
        model = Editor
        fields = ('agreement_number', 'editor_given', 'editor_date', 'secondary_date', )
        widgets = {
            'editor_date': forms.SelectDateWidget(),
            'secondary_date': forms.SelectDateWidget()
        }