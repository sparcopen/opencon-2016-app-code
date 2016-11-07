import json
import pytz

from datetime import datetime

from dal import autocomplete
from django.conf import settings
from django.core.urlresolvers import Http404
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.core.urlresolvers import reverse_lazy, reverse
from django.views.generic import FormView, TemplateView
from django.utils import timezone

from .forms import ApplicationForm
from .helpers import is_valid_email_address
from .models import Airport, Draft, Application, Institution, Organization, Country, Reference
from . import constants


# todo: find better solution for prefilling fields!
def post_to_json(post):
    dictionary = {}
    for key in post.keys():
        data = post.getlist(key)
        dictionary[key] = data
    return json.dumps(dictionary)


from .models import MULTIFIELD_NAMES
def load_json_to_initial(data):
    global MULTIFIELD_NAMES
    MULTIFIELD_NAMES += ['skills_0', 'gender_0', 'how_did_you_find_out_0', ]
    for key in data.keys():
        if key not in MULTIFIELD_NAMES:
            data[key] = data[key][0]

    data['skills'] = [data.get('skills_0', ''), data.get('skills_1', '')]
    data['gender'] = [data.get('gender_0', ''), data.get('gender_1', '')]
    data['how_did_you_find_out'] = [data.get('how_did_you_find_out_0', ''), data.get('how_did_you_find_out_1', '')]

    return data


class ApplicationView(FormView):
    """View shows the application itself"""
    form_class = ApplicationForm
    template_name = 'application/application_form.html'

    def get_referral(self, referral=None):
        if referral is None or not Reference.objects.filter(key=referral).exists():
            return {}
        reference = Reference.objects.get(key=referral)
        return {
            'image': reference.image,
            'name': reference.name,
            'text': reference.text,
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'action_url': self.request.get_full_path(),
            'organization': self.get_referral(self.kwargs.get('referral')),
        })
        return context

    def get_success_url(self):
        """Get the success url with the right primary key so a customized thank you message can be shown"""
        application_pk = self.application.pk
        return reverse('application:thank_you', kwargs={'pk': application_pk})

    def remove_form_errors(self, form):
        """Removes the errors from the form except for email and acknowledgement which is required for draft as well"""
        for field in form:
            if field.name in ['email', 'acknowledgements']:
                continue
            form.errors[field.name] = form.error_class()
        return form

    def save_draft(self, form):
        """
        Tries to save the draft. Checks whether the email and acknowledgement is valid.
        Returns the whether the draft was saved, the form itself and the the draft if it was created.
        """
        form = self.remove_form_errors(form)

        email = form.data['email']
        acknowledgements = form.data.getlist('acknowledgements')

        if is_valid_email_address(email) and len(acknowledgements) == 4:
            draft, created = Draft.objects.get_or_create(email=email)
            if created:
                draft.data = post_to_json(self.request.POST)
                draft.save()
                return True, form, draft

            form.add_error('email', 'An draft application associated with your e-mail address has '
                           'already been saved on our servers. If you cannot access it, contact us. ')
        return False, form, None

    def is_after_deadline(self):
        deadline_unaware = datetime.strptime(constants.APPLICATION_DEADLINE, '%Y/%m/%d %H:%M')
        deadline = pytz.utc.localize(deadline_unaware)

        referral = self.kwargs.get('referral', '')

        try:
            reference = Reference.objects.get(key=referral)
            if reference.deadline:
                deadline = reference.deadline
        except Reference.DoesNotExist:
            pass

        return timezone.now() > deadline

    def form_invalid(self, form):
        """
        Handles the form when it's invalid. For save,
        it tries to save a draft for submit it invokes super().form_invalid()
        """
        if '_save' in self.request.POST:
            valid, form, draft = self.save_draft(form)
            if valid:
                return render(self.request, 'application/form_saved.html', {'draft': draft})
        return super().form_invalid(form)

    def form_valid(self, form):
        """
        If the form was saved, it saves a draft and renders a info message.
        If the form was submitted, it saves it and set a inactive flag for draft.
        """
        if '_save' in self.request.POST:
            _, _, draft = self.save_draft(form)
            return render(self.request, 'application/form_saved.html', {'draft': draft})
        elif '_submit':
            self.application = form.save()
            email = form.data['email']
            if Draft.objects.filter(email=email).exists():
                draft = Draft.objects.get(email=email)
                draft.inactive = True
                draft.save()
            return super().form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        if self.is_after_deadline():
            return redirect(settings.REDIRECT_URL)

        return super().dispatch(request, *args, **kwargs)


class PreFilledApplicationView(ApplicationView):
    """View for handling the application with prefilled data from draft"""
    def get_draft(self):
        """Gets the draft based on uuid and raises a 404 if the draft does not exists"""
        try:
            draft_uuid = self.kwargs.get('uuid')
            draft = Draft.all_objects.get(uuid=draft_uuid)
            return draft
        except (ValueError, Draft.DoesNotExist):
            raise Http404

    def save_draft(self, form):
        """Saves the draft and makes sure the email wasn't changed"""
        form = self.remove_form_errors(form)
        draft_uuid = self.kwargs.get('uuid')
        draft = Draft.objects.get(uuid=draft_uuid)

        # Do not change email doesn't matter what
        mutable = self.request.POST._mutable
        self.request.POST._mutable = True
        self.request.POST['email'] = draft.email
        self.request.POST._mutable = mutable
        draft.data = post_to_json(self.request.POST)
        draft.save()
        return True, form, draft

    def get_initial(self):
        """Loads the initial data from draft"""
        draft = self.get_draft()
        draft_data = json.loads(draft.data)
        return load_json_to_initial(draft_data)

    def get(self, request, uuid, *args, **kwargs):
        draft = self.get_draft()
        if draft.inactive:
            return render(self.request, 'application/already_submitted.html', {})
        return super().get(request, *args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        data = json.loads(self.get_draft().data)
        referral = data.get('referred_by', [''])[0]
        self.kwargs['referral'] = referral
        return super().dispatch(request, *args, **kwargs)


class ReferralApplicationView(ApplicationView):
    """View shows the application with referral code"""
    def get_initial(self):
        referral = self.kwargs.get('referral')
        return {'referred_by': referral}


def check_email(request, email):
    if Application.objects.filter(email=email).exists():
        context = {}
        return render(request, 'application/popup_already_submitted.html', context)

    if Draft.objects.filter(email=email).exists():
        context = {'draft': Draft.objects.get(email=email)}
        return render(request, 'application/popup_saved_draft.html', context)

    context = {}
    return render(request, 'application/popup_alright.html', context)


def send_email(request, email):
    draft = get_object_or_404(Draft, email=email)
    status = draft.send_access()
    if status:
        template_name = 'application/access_sent.html'
    else:
        template_name = 'application/access_not_sent.html'
    return render(request, template_name, {})


class AirportAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Airport.objects.all()
        if self.q:
            qs = qs.filter(Q(name__icontains=self.q) | Q(iata_code__istartswith=self.q))
        return qs


class InstitutionAutocomplete(autocomplete.Select2QuerySetView):
    def has_add_permission(self, request):
        return True

    def get_queryset(self):
        qs = Institution.objects.filter(show=True)
        if self.q:
            qs = qs.filter(Q(name__icontains=self.q))
        return qs


class OrganizationAutocomplete(autocomplete.Select2QuerySetView):
    def has_add_permission(self, request):
        return True

    def get_queryset(self):
        qs = Organization.objects.filter(show=True)
        if self.q:
            qs = qs.filter(Q(name__icontains=self.q))
        return qs


class CountryAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Country.objects.all()
        if self.q:
            qs = qs.filter(Q(name__icontains=self.q))
        return qs


class ThankYou(TemplateView):
    template_name = 'application/thank_you.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'application': self.application})
        return context

    def get(self, request, pk, *args, **kwargs):
        self.application = get_object_or_404(Application, pk=pk)
        return redirect('http://www.opencon2016.org/thank_you?referral=' + str(self.application.my_referral))
        # return super().get(request, *args, **kwargs)
