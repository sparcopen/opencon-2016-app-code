from django import forms
from .models import Application, Airport, Institution, Organization, Country
from .forms_field_other import OptionalChoiceField, OptionalMultiChoiceField
from django.forms.widgets import CheckboxSelectMultiple, HiddenInput, RadioSelect, Select

from dal import autocomplete
import ast
from .data import *
from .models import STATUS_CHOICES


class ApplicationForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        if kwargs.get('instance'):
            kwargs['initial'] = {
                'occupation': ast.literal_eval(kwargs.get('instance').occupation or '[]'),
                'degree': ast.literal_eval(kwargs.get('instance').degree or '[]'),
                'participation': ast.literal_eval(kwargs.get('instance').participation or '[]'),
                'expenses': ast.literal_eval(kwargs.get('instance').expenses or '[]'),
                'opt_outs': ast.literal_eval(kwargs.get('instance').opt_outs or '[]'),
                'acknowledgements': ast.literal_eval(kwargs.get('instance').acknowledgements or '[]'),
            }

        super().__init__(*args, **kwargs)

        self.fields['gender'] = OptionalChoiceField(
            label='Gender^',
            choices=GENDER_CHOICES,
        )

        self.fields['skills'] = OptionalMultiChoiceField(
            choices=SKILLS_CHOICES,
            label='Do you have any of the following skills?^',
            help_text='Check all that apply.',
        )

        self.fields['how_did_you_find_out'] = OptionalMultiChoiceField(
            choices=HOW_DID_YOU_FIND_OUT_CHOICES,
            label='How did you find out about OpenCon 2016?^',
            help_text='Check all that apply.',
        )

        self.fields['airport'] = forms.ModelChoiceField(
            queryset=Airport.objects.all(),
            widget=autocomplete.ModelSelect2(url='application:airport-autocomplete'),
            label='Closest international airport to the city you indicated in the previous question.',
            help_text='This question helps us understand how for you would need to travel. Begin by '
                      'typing the name of the city and suggestions will show up. Click the correct one. '
                      'You can also search by the three-letter IATA code (for example “LHR” for London). '
                      'If your airport does not show up, please type “Other Airport” and specify your '
                      'airport in the comments box below. Please enter an airport regardless of how close '
                      'you are located to Washington, DC, and note that U.S. regional/national airports '
                      'are permitted.',
        )
        self.fields['institution'] = forms.ModelChoiceField(
            queryset=Institution.objects.all(),
            widget=autocomplete.ModelSelect2(url='application:institution-autocomplete'),
            label='Primary Institution / Employer / Affiliation',
            help_text='Begin by typing the full name (no abbreviations) of the primary institution or '
                      'organization where you work or go to school. A list of suggestions will show up '
                      'as you type. If the correct name appears, click to select. If it does not appear, '
                      'finish typing the full name and click the option to “Create” the name. You may need '
                      'to scroll down to find this option.',
        )
        self.fields['organization'] = forms.ModelChoiceField(
            queryset=Organization.objects.all(),
            widget=autocomplete.ModelSelect2(url='application:organization-autocomplete'),
            label='Other Primary Affiliation / Organization / Project (Optional)',
            help_text='If you have another primary affiliation or project, you may list it here. Similar to the '
                      'question above, begin by typing the full name. If the correct name shows up automatically, '
                      'click to select. If not, then finish typing and click “Create.” If you have multiple other '
                      'affiliations, list only the most important one here. You may list any additional '
                      'affiliations in the Comments Box at the end of the application.',
            required=False,
        )


    class Meta:
        model = Application
        fields = (
            'email',
            'first_name',
            'last_name',
            'nickname',
            'alternate_email',
            'twitter_username',
            'institution',
            'organization',
            'area_of_interest',
            'description',
            'interested',
            'goal',
            'participation',
            'participation_text',
            'citizenship',
            'residence',
            'gender',
            'occupation',
            'degree',
            'experience',
            'fields_of_study',
            # 'ideas',
            'skills',
            'how_did_you_find_out',
            # 'visa_requirements',
            'scholarship',
            'expenses',
            'location',
            'airport',
            'additional_info',
            'opt_outs',
            'acknowledgements',
            'referred_by',
        )
        widgets = {
            'referred_by': HiddenInput,
            'occupation': CheckboxSelectMultiple(choices=OCCUPATION_CHOICES),
            'experience': RadioSelect(choices=EXPERIENCE_CHOICES),
            'citizenship': Select(choices=COUNTRY_CHOICES),
            'residence': Select(choices=COUNTRY_CHOICES),
            'fields_of_study': Select(choices=FIELDS_OF_STUDY_CHOICES),
            'degree': CheckboxSelectMultiple(choices=DEGREE_CHOICES),
            'area_of_interest': RadioSelect(choices=AREA_OF_INTEREST_CHOICES),
            'participation': CheckboxSelectMultiple(choices=PARTICIPATION_CHOICES),
            # 'visa_requirements': RadioSelect(choices=VISA_CHOICES),
            'expenses': CheckboxSelectMultiple(choices=EXPENSES_CHOICES),
            'scholarship': RadioSelect,
            'opt_outs': CheckboxSelectMultiple(choices=OPT_OUTS_CHOICES),
            'acknowledgements': CheckboxSelectMultiple(choices=ACKNOWLEDGEMENT_CHOICES),
        }


class ChangeStatusAdminForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ('status', 'status_reason')
        widgets = {
            'status': Select(choices=STATUS_CHOICES),
        }
