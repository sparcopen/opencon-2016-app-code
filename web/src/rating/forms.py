from application.models import STATUS_CHOICES
from django import forms
from django.forms import widgets
from .models import Step1Rating, Step2Rating
from .models import RATING_METADATA_1_CHOICES, RATING_METADATA_2_CHOICES

import ast


class Step1RateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        if kwargs.get('instance'):
            kwargs['initial'] = {
                'rating_metadata_1': ast.literal_eval(kwargs.get('instance').rating_metadata_1 or '[]'),
            }

        super().__init__(*args, **kwargs)

    class Meta:
        model = Step1Rating
        fields = [
            'application',
            'rating',
            'acceptance',
            'acceptance_reason',
            'rating_metadata_1',
        ]
        widgets = {
            'application': widgets.HiddenInput,
            'rating_metadata_1': widgets.CheckboxSelectMultiple(choices=RATING_METADATA_1_CHOICES),
        }

    def clean_acceptance_reason(self):
        reason = self.cleaned_data['acceptance_reason']
        if self.cleaned_data['acceptance'] == 'yes' and not reason:
            raise forms.ValidationError('This field is required.')
        return reason


class Step2RateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        if kwargs.get('instance'):
            kwargs['initial'] = {
                'rating_metadata_2': ast.literal_eval(kwargs.get('instance').rating_metadata_2 or '[]'),
            }

        super().__init__(*args, **kwargs)

    class Meta:
        model = Step2Rating
        fields = [
            'application',
            'rating',
            'acceptance',
            'acceptance_reason',
            'rating_metadata_2',
        ]
        widgets = {
            'application': widgets.HiddenInput,
            'rating_metadata_2': widgets.CheckboxSelectMultiple(choices=RATING_METADATA_2_CHOICES),
        }

    def clean_acceptance_reason(self):
        reason = self.cleaned_data['acceptance_reason']
        if self.cleaned_data['acceptance'] == 'yes' and not reason:
            raise forms.ValidationError('This field is required.')
        return reason


class ChangeStatusForm(forms.Form):
    STATUS_CHOICES_NO_DELETED = STATUS_CHOICES[:-1]
    choice = forms.ChoiceField(choices=STATUS_CHOICES_NO_DELETED, label='Current status')
    reason = forms.CharField(widget=widgets.Textarea, required=False)
    application = forms.CharField(widget=forms.HiddenInput)
