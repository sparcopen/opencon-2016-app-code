from django.conf import settings
from django.conf.urls import url
from django.views.generic.base import RedirectView
from . import views
from .models import Institution, Organization


urlpatterns = [
    # #todo -- instead of hard-coded `url='/apply/'` use a reference to the view name (reverse_lazy?)
    url(r'^$', RedirectView.as_view(url='/apply/', permanent=False), name='root'),
    url(r'^apply/$', views.ApplicationView.as_view(), name='application'),
    url(r'^check_email/(?P<email>[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)$',
        views.check_email, name='check_email'),
    url(r'^send_email/(?P<email>[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)$',
        views.send_email, name='send_email'),
    url(r'^airport-autocomplete/$', views.AirportAutocomplete.as_view(), name='airport-autocomplete'),
    url(r'^country-autocomplete/$', views.CountryAutocomplete.as_view(), name='country-autocomplete'),
    url(r'^institution-autocomplete/$',
        views.InstitutionAutocomplete.as_view(
            model=Institution,
            create_field='name',
        ),
        name='institution-autocomplete'),
    url(r'^organization-autocomplete/$',
        views.OrganizationAutocomplete.as_view(
            model=Organization,
            create_field='name',
        ),
        name='organization-autocomplete'),
    url(r'^referral/(?P<referral>\w{1,' + str(settings.MAX_CUSTOM_REFERRAL_LENGTH) + '})$',
        views.ReferralApplicationView.as_view(), name='referral'),
    url(r'^saved/(?P<uuid>[^/]+)/$', views.PreFilledApplicationView.as_view(), name='access_draft'),
    url(r'^thank-you/(?P<pk>\d+)', views.ThankYou.as_view(), name='thank_you'),
]
