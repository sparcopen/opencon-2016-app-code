import math
import uuid

from django.conf import settings
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.db import models
from django.template.loader import render_to_string
from .validators import rating_validator


RATING_METADATA_1_CHOICES = [
    ('needs_followup', 'This application includes interesting projects or ideas that should be followed up on (include notes above)'),
    ('strong_application', 'This is an especially strong application and it should be sent to the Organizing Committee immediately'),
    ('know_applicant_or_conflict', 'I personally know this applicant or have a conflict of interest'),
    ('problem_spotted', 'There is a problem with this application'),
]

RATING_METADATA_2_CHOICES = [
    ('award_certificate', 'This applicant has done meaningful work to advance Open Access, Open Education or Open Data and should be awarded a certificate'),
    ('add_to_shortlist', 'This applicant should be added to the short list'),
    ('know_applicant_or_conflict', 'I personally know this applicant or have a conflict of interest'),
    ('problem_spotted', 'There is a problem with this application'),
]


class TimestampMixin(models.Model):
    """ Mixin for saving the creation time and the time of the last update """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class User(TimestampMixin, models.Model):
    """
    Users allowed to rate applications.
    """
    uuid = models.UUIDField(default=uuid.uuid4)
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    nick = models.CharField(max_length=200, blank=True, null=True)
    email = models.EmailField()

    is_round_1_reviewer = models.BooleanField(default=True)
    is_round_2_reviewer = models.BooleanField(default=False)

    organizer = models.BooleanField(default=False)
    invitation_sent = models.BooleanField(default=False)

    disabled_at = models.DateTimeField(blank=True, null=True)

    def invite(self):
        """
        Send invite mail to application email address.
        """
        if not settings.REVIEWER_MAIL_ENABLED:
            return

        context = {
            "user": self,
            "link": "{}{}".format(
                settings.BASE_URL,
                reverse("rating:rate", args=[self.uuid])
            )
        }

        subject = render_to_string(
            "rating/email/invite.subject", context
        ).strip()
        message = render_to_string("rating/email/invite.message", context)

        send_mail(
            subject,
            message,
            settings.FROM_MAIL,
            [self.email],
            fail_silently=False
        )
        self.invitation_sent = True
        self.save()

    def __str__(self):
        return self.nick

    def avg(self):
        count = self.rated.count()
        if count == 0:
            return 0

        return sum(rating.rating for rating in self.rated.all()) / count

    def avg2(self):
        count = self.rated2.count()
        if count == 0:
            return 0

        return sum(rating.rating for rating in self.rated2.all()) / count

    def standard_deviation(self):
        count = self.rated.count()
        if count == 0:
            return 0

        ratings = self.rated.all()
        mean = sum(rating.rating for rating in ratings) / count
        sm = sum((mean-rating.rating)**2 for rating in ratings)
        return math.sqrt(sm/count)

    def standard_deviation2(self):
        count = self.rated2.count()
        if count == 0:
            return 0

        ratings = self.rated2.all()
        mean = sum(rating.rating for rating in ratings) / count
        sm = sum((mean-rating.rating)**2 for rating in ratings)
        return math.sqrt(sm/count)


STATE_CHOICES = (
    (True, u'Yes'),
    (False, u'No'),
)


class Step1Rating(TimestampMixin, models.Model):
    """
    Application rating.
    """
    created_by = models.ForeignKey(
        User,
        related_name="rated"
    )
    application = models.ForeignKey(
        "application.Application",
        related_name="ratings"
    )
    rating = models.DecimalField(
        verbose_name='How would you rate this application?',
        help_text='Please either enter whole numbers (e.g. 6) or enter decimal numbers up to one place using '
                  'a period (e.g. 6.7). Note the system may reject decimals entered using a comma.',
        decimal_places=1,
        max_digits=3,
        validators=[rating_validator]
    )
    ACCEPTANCE_CHOICE = [
        ('yes', 'Yes'),
        ('neutral', 'Neutral'),
        ('no', 'No')
    ]
    acceptance = models.CharField(
        verbose_name='Do you think this application should be considered for acceptance?',
        choices=ACCEPTANCE_CHOICE,
        default=ACCEPTANCE_CHOICE[1][0],
        max_length=10,
    )
    acceptance_reason = models.TextField(
        verbose_name='Please explain why this application should/shouldn’t be considered to acceptance:',
        help_text='This question is mandatory if you answered Yes to question 2. If you said No or Neutral, '
                  'you can either explain your answer or leave it blank.',
        blank=True, null=True,
    )
    rating_metadata_1 = models.TextField(
        verbose_name='Please check below if any apply:',
        help_text='',
        blank=True, null=True,
    )
    # #todo -- consider removing comments from the model (they aren't being used at the moment)
    comments = models.TextField(
        verbose_name='Any other comments?',
        blank=True, null=True,
    )

    ipaddress = models.GenericIPAddressField(blank=True, null=True)

    def save(self, *args, **kwargs):
        obj = super().save(*args, **kwargs)
        self.application.save()  # when save is envoked ratings are recalculated
        return obj


class Step2Rating(TimestampMixin, models.Model):
    """
    Application rating.
    """
    created_by = models.ForeignKey(
        User,
        related_name="rated2"
    )
    application = models.ForeignKey(
        "application.Application",
        related_name="ratings2"
    )
    rating = models.DecimalField(
        verbose_name='How would you rate this application?',
        help_text='Please either enter whole numbers (e.g. 6) or enter decimal numbers up to one place using '
                  'a period (e.g. 6.7). Note the system may reject decimals entered using a comma.',
        decimal_places=1,
        max_digits=3,
        validators=[rating_validator]
    )
    ACCEPTANCE_CHOICE = [
        ('yes', 'Yes'),
        ('neutral', 'Neutral'),
        ('no', 'No')
    ]
    acceptance = models.CharField(
        verbose_name='Do you think this application should be considered for acceptance?',
        choices=ACCEPTANCE_CHOICE,
        default=ACCEPTANCE_CHOICE[1][0],
        max_length=10,
    )
    acceptance_reason = models.TextField(
        verbose_name='Please explain why this application should/shouldn’t be considered to acceptance:',
        help_text='This question is mandatory if you answered Yes to question 2. If you said No or Neutral, '
                  'you can either explain your answer or leave it blank.',
        blank=True, null=True,
    )
    rating_metadata_2 = models.TextField(
        verbose_name='Please check below if any apply:',
        help_text='',
        blank=True, null=True,
    )
    # #todo -- consider removing comments from the model (they aren't being used at the moment)
    comments = models.TextField(
        verbose_name='Any other comments?',
        blank=True, null=True,
    )

    ipaddress = models.GenericIPAddressField(blank=True, null=True)

    def save(self, *args, **kwargs):
        obj = super().save(*args, **kwargs)
        self.application.save()  # when save is envoked ratings are recalculated
        return obj
