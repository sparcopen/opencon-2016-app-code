from django.conf import settings
from django.core.urlresolvers import reverse_lazy
from django.db.models import Count
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View, TemplateView, ListView

from application.models import Application

from .forms import Step1RateForm, Step2RateForm, ChangeStatusForm
from .models import User, Step1Rating, Step2Rating

from abc import ABC, abstractproperty, abstractmethod

from application.models import DISPLAYED_FIELDS_ROUND_1, DISPLAYED_FIELDS_ROUND_2


class AuthenticatedMixin(View, ABC):

    @abstractproperty
    def permission(self):
        pass

    def get(self, request, *args, **kwargs):
        if self.permission is None:
            raise AssertionError('Permission level was not set.')
        self.get_user(request)  # is logged in?
        return super().get(request, *args, **kwargs)

    def get_user(self, request=None):
        if request is not None:
            user_pk = request.session.get('user_pk')
            self.user = get_object_or_404(User, pk=user_pk, disabled_at=None)

        if not hasattr(self, 'user'):
            raise AssertionError(
                'You are trying to get the user but you have to invoke this function with request first.'
            )

        if self.permission == 1 and self.user.is_round_1_reviewer:
            return self.user
        elif self.permission == 2 and self.user.is_round_2_reviewer:
            return self.user
        raise Http404

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({'user': self.user})
        return context


class Login(View):
    def get(self, request, uuid):
        user = get_object_or_404(User, uuid=uuid)
        request.session['user_pk'] = user.pk
        if user.is_round_1_reviewer:
            return redirect('rating:rate_round1')
        elif user.is_round_2_reviewer:
            return redirect('rating:rate_round2')
        raise Http404


class Logout(View):
    def get(self, request):
        del request.session['user_pk']
        return redirect('rating:logged_out')


class AbstractRateView(AuthenticatedMixin, View, ABC):
    displayed_data = DISPLAYED_FIELDS_ROUND_1

    @abstractproperty
    def rate_form_class(self):
        pass

    @abstractproperty
    def skip_url(self):
        pass

    @abstractmethod
    def rate(self, request, user, rating_pk):
        pass

    @abstractmethod
    def get(self, request, rating_pk=None):
        pass

    def get_context_data(self, created_by, application, rate_form=None):
        if not rate_form:
            rate_form = self.rate_form_class(
                initial={
                    'created_by': created_by.id,
                    'application': application.id,
                }
            )
        context = {
            'user': created_by,
            'rate_count': created_by.rated.count(),
            'application_data': application.get_data(self.displayed_data),
            'forms': {
                'rate': rate_form,
                'status': ChangeStatusForm(
                    initial={
                        'choice': application.status,
                        'application': application.pk
                    }
                ),
            },
            'skip_url': self.skip_url,
        }

        return context

    def change_status(self, request, user, rating_pk):
        application = get_object_or_404(Application, pk=request.POST['application'])

        form = ChangeStatusForm(request.POST)
        if user.organizer and form.is_valid():
            ip = request.META.get('HTTP_X_REAL_IP') or request.META['REMOTE_ADDR']
            application.change_status(form.cleaned_data['choice'], user, ip, form.cleaned_data['reason'])

        return self.get(request, rating_pk)

    def post(self, request, rating_pk=None):
        user = super().get_user(request)
        if request.POST.get('choice'):
            return self.change_status(request, user, rating_pk)
        else:
            return self.rate(request, user, rating_pk)


class RateView(AbstractRateView):
    rate_form_class = Step1RateForm
    permission = 1
    skip_url = reverse_lazy('rating:rate_round1')

    def get(self, request, rating_pk=None):
        user = super().get_user(request)

        if rating_pk is None:
            unrated = Application.objects.get_unrated(user).order_by('?').first()
        else:
            unrated = get_object_or_404(Step1Rating, pk=rating_pk, created_by=user)
            if not unrated.application.need_rating1:
                return render(request, 'rating/cannot_rate.html', context={'user': user})

        if unrated:
            template_name = 'rating/rate.html'

            if rating_pk is None:
                context = self.get_context_data(user, unrated)
            else:
                rate_form = Step1RateForm(instance=unrated)
                context = self.get_context_data(user, unrated.application, rate_form)
        else:
            template_name = 'rating/all_rated.html'
            context = {'user': user}

        return render(request, template_name, context=context)

    def rate(self, request, user, rating_pk):
        if rating_pk is None:
            rate_form = Step1RateForm(request.POST)
        else:
            rating = get_object_or_404(Step1Rating, pk=rating_pk, created_by=user)
            rate_form = Step1RateForm(request.POST, instance=rating)

        if rate_form.is_valid():
            rating = rate_form.save(commit=False)
            rating.created_by = user
            rating.ipaddress = request.META.get('HTTP_X_REAL_IP') or request.META['REMOTE_ADDR']
            rating.save()
        else:
            application = rate_form.cleaned_data['application']
            context = self.get_context_data(user, application, rate_form=rate_form)
            return render(request, 'rating/rate.html', context=context)

        return redirect('rating:rate_round1')


class AbstractRate2View(AbstractRateView):
    permission = 2
    rate_form_class = Step2RateForm
    skip_url = reverse_lazy('rating:rate_round2')
    displayed_data = DISPLAYED_FIELDS_ROUND_2
    # displayed_data = None  # for displaying all the data

    def get_context_data(self, created_by, application, rate_form=None):
        context = super().get_context_data(created_by, application, rate_form)
        all_reviews = application.ratings2.all()
        context.update({'all_reviews': all_reviews})
        return context


class Rate2View(AbstractRate2View):
    def get(self, request, rating_pk=None):
        user = super().get_user(request)
        context = {'user': user}
        template_name = 'rating/rate.html'
        if rating_pk is None:  # new rating
            application = Application.objects.get_unrated2(user).order_by('?').first()
            if application:
                context = self.get_context_data(user, application)
            else:
                template_name = 'rating/all_rated.html'
        else:  # old rating
            rating = get_object_or_404(Step2Rating, pk=rating_pk, created_by=user)
            rate_form = Step2RateForm(instance=rating)
            context = self.get_context_data(user, rating.application, rate_form)

        return render(request, template_name, context=context)

    def rate(self, request, user, rating_pk):
        if rating_pk is None:
            rate_form = Step2RateForm(request.POST)
        else:
            rating = get_object_or_404(Step2Rating, pk=rating_pk, created_by=user)
            rate_form = Step2RateForm(request.POST, instance=rating)

        if rate_form.is_valid():
            rating = rate_form.save(commit=False)
            rating.created_by = user
            rating.ipaddress = request.META.get('HTTP_X_REAL_IP') or request.META['REMOTE_ADDR']
            rating.save()
        else:
            application = rate_form.cleaned_data['application']
            context = self.get_context_data(user, application, rate_form=rate_form)
            return render(request, 'rating/rate.html', context=context)

        return redirect('rating:rate_round2')


class Rate2SelectView(AbstractRate2View):
    def get(self, request, rating_pk):
        user = super().get_user(request)
        application = Application.objects.get(pk=rating_pk)

        try:
            old_rating = Step2Rating.objects.get(application=application, created_by=user)
            rate_form = Step2RateForm(instance=old_rating)
            context = self.get_context_data(user, application, rate_form)
        except Step2Rating.DoesNotExist:
            context = self.get_context_data(user, application)

        return render(request, 'rating/rate.html', context=context)

    def rate(self, request, user, application_pk):
        application = Application.objects.get(pk=application_pk)

        try:
            old_rating = Step2Rating.objects.get(application=application, created_by=user)
            rate_form = Step2RateForm(request.POST, instance=old_rating)
        except Step2Rating.DoesNotExist:
            rate_form = Step2RateForm(request.POST)

        if rate_form.is_valid():
            rating = rate_form.save(commit=False)
            rating.created_by = self.get_user()
            rating.ipaddress = request.META.get('HTTP_X_REAL_IP') or request.META['REMOTE_ADDR']
            rating.save()
        else:
            context = self.get_context_data(user, application, rate_form=rate_form)
            return render(request, 'rating/rate.html', context=context)

        return redirect('rating:previous2', rating_pk=application.pk)


class Stats(AuthenticatedMixin, TemplateView):
    template_name = 'rating/stats.html'
    permission = 1

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        users = User.objects.annotate(finished_count=Count('rated')).prefetch_related('rated')
        users = users.filter(finished_count__gte=1).order_by('-finished_count')[:settings.LEADERBOARD_ROUND1_MAX_DISPLAYED]
        context.update({'ranking': users})
        return context


class Stats2(AuthenticatedMixin, TemplateView):
    template_name = 'rating/stats2.html'
    permission = 2

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        users = User.objects.annotate(finished_count2=Count('rated2')).prefetch_related('rated2')
        users = users.filter(finished_count2__gte=1).order_by('-finished_count2')[:settings.LEADERBOARD_ROUND2_MAX_DISPLAYED]
        context.update({'ranking': users})
        return context


class PreviousRatings(AuthenticatedMixin, ListView):
    template_name = 'rating/ratings_list.html'
    permission = 1

    def get_queryset(self):
        user = self.get_user()
        return Step1Rating.objects.filter(created_by=user).prefetch_related('application', 'application__institution')


class AllRound2(AuthenticatedMixin, ListView):
    template_name = 'rating/application_list.html'
    permission = 2

    def get_queryset(self):
        return Application.objects.get_all_round2().prefetch_related('institution')

    def get_context_data(self, **kwargs):
        user_id = self.get_user().pk
        user = User.objects.prefetch_related('rated2', 'rated2__application').get(pk=user_id)
        context = super().get_context_data(**kwargs)
        context.update({'user': user})
        return context
