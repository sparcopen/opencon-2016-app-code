"""
Application urlconfig
"""
from django.conf.urls import url

from . import views


urlpatterns = [
    url(
        r'^login/(?P<uuid>[0-9a-f-]{32})/$',
        views.Login.as_view(),
        name='login',
    ),
    url(
        r"^logout/$",
        views.Logout.as_view(),
        name="logout"
    ),

    url(
        r"^round1/$",
        views.RateView.as_view(),
        name="rate_round1"
    ),
    url(
        r"^round2/$",
        views.Rate2View.as_view(),
        name="rate_round2"
    ),
    url(
        r"^stats/$",
        views.Stats.as_view(),
        name="stats"
    ),
    url(
        r"^stats2/$",
        views.Stats2.as_view(),
        name="stats2"
    ),

    url(
        r"^old/$",
        views.PreviousRatings.as_view(),
        name="previous"
    ),
    url(
        r"^all2/$",
        views.AllRound2.as_view(),
        name="all2"
    ),

    url(
        r"^old2/(?P<rating_pk>[0-9]+)/$",
        views.Rate2SelectView.as_view(),
        name="previous2"
    ),

    url(
        r'^logged_out/$',
        views.TemplateView.as_view(template_name='rating/logged_out.html'),
        name='logged_out'
    ),

    url(
        r"^old/(?P<rating_pk>[0-9]+)/$",
        views.RateView.as_view(),
        name="previous"
    ),
]
