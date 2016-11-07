import string
import uuid
import random
import datetime

from django.conf import settings
from django.core.mail import EmailMessage
from django.core.validators import MinLengthValidator
from django.db import models
from django.db.models import Q
from django.template.loader import render_to_string
from django.utils import timezone
from .validators import MaxChoicesValidator, MinChoicesValidator, EverythingCheckedValidator, none_validator

from .data import *
from .constants import *


STATUS_CHOICES = [
    ('regular', 'Regular'),  # First one is default
    ('blacklisted', 'Blacklist'),
    ('whitelist2', 'Whitelist for round 2'),
    ('whitelist3', 'Whitelist for round 3'),
    ('deleted', 'Deleted'),
]


class HideInactive(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(inactive=False)


class TimestampMixin(models.Model):
    """ Mixin for saving the creation time and the time of the last update """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Draft(TimestampMixin, models.Model):
    email = models.EmailField(unique=True)
    data = models.TextField()
    uuid = models.UUIDField(default=uuid.uuid4)
    inactive = models.BooleanField(default=False)
    sent_email_data = models.DateTimeField(blank=True, null=True)

    objects = HideInactive()
    all_objects = models.Manager()

    def __str__(self):
        return self.email

    def send_access(self):
        if self.sent_email_data:
            can_send = timezone.now() - self.sent_email_data > datetime.timedelta(minutes=settings.SEND_ACCESS_INTERVAL)
        else:
            can_send = True

        if can_send:
            self.sent_email_data = timezone.now()
            self.save()
            if settings.SEND_EMAILS:
                message = render_to_string('application/email/draft.txt', {'uuid': self.uuid, 'email': self.email,})
                email = EmailMessage(
                    subject='OpenCon 2016 Draft Application',
                    body=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[self.email],
                )
                email.content_subtype = "html"
                email.send(fail_silently=True)
            return True
        return False


class Airport(models.Model):
    iata_code = models.CharField(max_length=10)
    name = models.CharField(max_length=100)

    def __str__(self):
        return '[{}] {}'.format(self.iata_code, self.name)


class Institution(models.Model):
    name = models.CharField(max_length=300)
    show = models.BooleanField(default=False)  # shown in autocomplete or not

    def __str__(self):
        return self.name


class Organization(models.Model):
    name = models.CharField(max_length=300)
    show = models.BooleanField(default=False)  # shown in autocomplete or not

    def __str__(self):
        return self.name


class Country(models.Model):
    name = models.CharField(max_length=120)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Countries'

# todo: update this form
MULTIFIELD_NAMES = ['occupation', 'degree', 'participation', 'gender', 'expenses', 'skills', 'opt_outs', 'acknowledgements', ]
DISPLAYED_FIELDS_ROUND_1 = ['first_name', 'last_name', 'institution', 'organization', 'area_of_interest', 'description', 'interested', 'goal', 'participation', 'participation_text', 'citizenship', 'residence', 'occupation', 'degree', 'experience', 'fields_of_study', 'additional_info', 'twitter_username',]
DISPLAYED_FIELDS_ROUND_2 = ['first_name', 'last_name', 'institution', 'organization', 'area_of_interest', 'description', 'interested', 'goal', 'participation', 'participation_text', 'citizenship', 'residence', 'occupation', 'degree', 'experience', 'fields_of_study', 'scholarship', 'additional_info', 'twitter_username',]

class ApplicationManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().exclude(status='deleted')

    def get_all(self):
        return super().get_queryset()

    def get_unrated(self, user):
        return self.get_queryset().filter(need_rating1=True).exclude(ratings__created_by=user)

    def get_unrated2(self, user):
        return self.get_all_round2().filter(need_rating2=True).exclude(ratings2__created_by=user)

    def get_all_round2(self):
        queryset = self.get_queryset().filter(need_rating1=False)
        return queryset.filter(Q(rating1__gte=NEEDED_RATING_TO_ROUND2) | Q(status__exact='whitelist2'))


class Application(TimestampMixin, models.Model):
    # field no. 1
    email = models.EmailField(
        verbose_name='E-Mail Address',
        help_text='Please fill in your e-mail address and click “Start Application” to unlock the rest of the form.',
        unique=True,
    )
    # field no. 2
    first_name = models.CharField(
        verbose_name='First / Given Name',
        max_length=50,
    )
    # field no. 3
    last_name = models.CharField(
        verbose_name='Last / Family Name',
        max_length=50,
    )
    # field no. 4
    nickname = models.CharField(
        verbose_name='Nickname / Preferred Name (Optional)',
        help_text='If you would like us to call you something different than the first name you entered above, '
                  'please tell us here. For example, if your name is “Michael” and you want to be called “Mike.”',
        max_length=50,
        blank=True, null=True,
    )
    # field no. 5
    alternate_email = models.EmailField(
        verbose_name='Alternate E-mail Address (Optional)',
        help_text='If you use another e-mail address that you would like to have on record, please enter it '
                  'here. We will only use this address if we cannot reach you at the address you provided above.',
        blank=True, null=True,
    )
    # field no. 6
    twitter_username = models.CharField(
        verbose_name='Twitter Username (Optional)',
        help_text='Include the username only, for example “@open_con”.',
        max_length=50,
        blank=True, null=True,
    )
    # field no. 7
    institution = models.ForeignKey(  # update the related name and verbose name in forms.py
        'Institution',
        related_name='person',
        blank=True, null=True,
    )
    # field no. 8
    # #todo -- consider renaming "organization" (affiliation_2?) + also "institution" (affiliation_1?)
    organization = models.ForeignKey(  # update the related name and verbose name in forms.py
        'Organization',
        related_name='person',
        blank=True, null=True,
    )
    # field no. 9
    area_of_interest = models.TextField(
        verbose_name='What is your primary area of interest?^',
        help_text='If there are multiple areas you are interested in, please select the one that best describes '
                  'your interest. Please note that OpenCon focuses on these issues in the specific context of '
                  'research and education.',
    )
    # field no. 10
    description = models.TextField(
        verbose_name='Describe yourself in 1-2 sentences.',
        help_text='Maximum 280 characters (~40 words). It’s up to you what information to provide. Many people '
                  'write something similar to their Twitter or Facebook bio.',
        max_length=280,
        validators=[MinLengthValidator(10)],
    )
    # field no. 11
    interested = models.TextField(
        verbose_name='Why are you interested in Open Access, Open Education and/or Open Data and how does it '
                     'relate to your work? If you are already involved in these issues, tell us how.',
        help_text='Maximum 1600 characters (~250 words). There are many reasons why Open is important. This '
                  'question is asking specifically why Open is important to *you*. Please use your own words '
                  'to describe your perspective and experience.',
        max_length=1600,
        validators=[MinLengthValidator(10)],
    )
    # field no. 12
    goal = models.TextField(
        verbose_name='The biggest goal of OpenCon is to catalyze action. What ideas do you have for advancing '
                     'Open Access, Open Education and/or Open Data, and how would you use your experience at '
                     'OpenCon to have an impact?',
        help_text='Maximum 1600 characters (~250 words).',
        max_length=1600,
        validators=[MinLengthValidator(10)],
    )
    # field no. 13
    # this is an optional question where we don't mention "(Optional)" in the verbose_name
    participation = models.TextField(
        verbose_name='Are you planning to participate in any of the following events in the next year? Have '
                     'you participated in any of them in the past?^',
        help_text='Check all that apply.',
        validators=[MinChoicesValidator(1), none_validator],
    )
    # field no. 14
    participation_text = models.TextField(
        verbose_name='For the events you checked, please explain how you participated and/or how you plan to '
                     'participate.',
        help_text='Maximum 600 characters (~100 words).',
        max_length=600,
        blank=True, null=True,
    )
    # field no. 15 (formerly 16)
    citizenship = models.TextField(
        verbose_name='Country of Citizenship^',
        help_text='Please select the country where you are a citizen (i.e. where your passport is from). If your '
                  'country isn’t listed, select “Country Not Listed” and indicate your country in the Comments '
                  'Box at the end of the application form.',
    )
    # field no. 16 (formerly 17)
    residence = models.TextField(
        verbose_name='Country of Residence^',
        help_text='Please select the country where you currently reside. If you are a resident of multiple '
                  'countries, pick the one where you will spend the most time this year. If your country isn’t '
                  'listed, see the previous question for instructions.',
    )
    # field no. 17 (formerly 15)
    # Has special field
    gender = models.CharField(
        max_length=80
    )
    # field no. 18
    occupation = models.TextField(
        verbose_name='What is your primary occupation?^',
        help_text='Please check the occupation that best describes what you do. If there are multiple options '
                  'that equally describe you, you may select up to three.',
        validators=[MaxChoicesValidator(3), none_validator],
    )
    # field no. 19
    degree = models.TextField(
        verbose_name='Which academic degrees have you attained, if any?^',
        help_text='Only check the degrees you have already been awarded. Note that there are no minimum academic '
                  'requirements to attend OpenCon, this question just helps us understand more about you.',
        validators=[none_validator],
    )
    # field no. 20
    experience = models.TextField(
        verbose_name='How many years have you worked in a career full time? For the purposes of this question, '
                     'please do *not* include time when you were a full time student or working full time as '
                     'a PhD candidate.^',
        help_text='If you have worked in multiple careers, please add the years together. Note that there is no '
                  'minimum career experience required to attend OpenCon, this question just helps us understand '
                  'more about you.',
        max_length=80,
    )
    # field no. 21
    fields_of_study = models.TextField(
        verbose_name='Which option below best describes your field of expertise or study?^',
        # #fyi -- "none_validator" not needed for this field -- this is Select, not CheckboxSelectMultiple
    )
    # field no. x (DELETED)
    # ideas = models.TextField(
    #     verbose_name='What ideas do you have for getting involved in Open Access, Open Education and/or Open Data? '
    #                  'If you are already involved, tell us how.',
    #     help_text='Maximum 1200 characters (~200 words).',
    #     max_length=1200,
    #     validators=[MinLengthValidator(10)],
    # )
    # field no. 22
    skills = models.TextField(
        # verbose_name and help_text are defined in forms.py
    )
    # field no. 23
    how_did_you_find_out = models.TextField(
        # verbose_name and help_text are defined in forms.py
        blank=True, null=True,
    )
    # # field no. x (DELETED)
    # visa_requirements = models.TextField(
    #     verbose_name='Visa requirements',
    #     help_text='Please review information on U.S. Visa eligibility and the Visa Waiver Program (ESTA) select '
    #               'the option below that best describes you. Note that requirements have recently changed. If you '
    #               'are still not sure, select “I’m not sure”.',
    # )
    # field no. 24
    # #todo -- rename field more appropriately?
    scholarship = models.CharField(
        verbose_name='OpenCon is a global event that seeks to bring together participants regardless of their '
                     'ability to pay for travel and expenses. Therefore, we seek to allocate our limited '
                     'scholarship funding carefully to the participants who need it most. How likely would '
                     'you be able to raise or contribute funding to your attendance at OpenCon 2016 if invited?',
        help_text='If you are applying for a sponsored scholarship from a university or organization, please select '
                  '“I couldn’t cover any of my expenses and could only attend if a full scholarship is provided.”',
        choices=(
            ('i_can_pay_everything', 'I could cover all of my expenses and do not need any scholarship funding'),
            ('i_can_pay_large_part', 'I could likely cover a large part of my expenses'),
            ('i_can_pay_small_part', 'I could likely cover a small part of my expenses'),
            ('i_can_pay_nothing',    'I couldn’t cover any of my expenses and could only attend if a full scholarship is provided'),
        ),
        default=None,
        max_length=20, # longest string above ('i_can_pay_everything') is 20 characters long
    )
    # field no. 25
    expenses = models.TextField(
        verbose_name='Which expenses would you need a scholarship to pay for?',
        help_text='Please select the expenses for which you would need scholarship funding in order to attend. If you are applying '
                  'for a sponsored scholarship from a university or organization, please select all of the expenses below. Please '
                  'note that scholarships do not include incidental expenses such as airport transit or meals outside of the conference.',
        validators=[none_validator],
    )
    # field no. 26
    location = models.CharField(
        verbose_name='OpenCon 2016 takes place in Washington, DC. If invited to attend, what city would you travel '
                     'to and from to get there?',
        help_text='Please list city, state/province (if applicable) AND country. For example, “San Francisco, '
                  'CA, United States”.',
        max_length=200,
    )
    # field no. 27
    airport = models.ForeignKey(
        'Airport',
        # verbose_name and help_text are defined in forms.py
    )
    # field no. 28
    additional_info = models.TextField(
        verbose_name='Comments Box (Optional)',
        help_text='Use this box for any additional information you would like to share about yourself, '
                  'projects you work on, or other information that could impact your attendance or participation '
                  'at OpenCon 2016, if invited. Maximum 900 characters, ~150 words.',
        max_length=900,
        blank=True, null=True
    )
    # field no. 29
    opt_outs = models.TextField(
        verbose_name='Opt-Outs',
        help_text='Please check the boxes below to opt-out.',
        blank=True, null=True
    )
    # field no. 30
    acknowledgements = models.TextField(
        help_text='Please check the boxes below to acknowledge your understanding. All boxes must be checked. '
                  'To review OpenCon’s Privacy Policy, click here: http://www.opencon2016.org/privacy',
        validators=[EverythingCheckedValidator(len(ACKNOWLEDGEMENT_CHOICES))],
    )

    referred_by = models.CharField(
        max_length=settings.MAX_CUSTOM_REFERRAL_LENGTH,
        blank=True, null=True,
    )

    my_referral = models.CharField(
        max_length=10,
    )

    data_sent_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args):
        if not self.my_referral:
            possible_characters = string.ascii_letters + string.digits
            self.my_referral = ''.join(random.choice(possible_characters) for _ in range(5))

        self.recalculate_ratings()

        if self.data_sent_at is None:
            self.data_sent_at = timezone.now()
            self.send_data_by_mail()

        super().save(*args)

    def __str__(self):
        return self.full_name()

    def full_name(self):
        return ' '.join([self.first_name, self.last_name])

    def send_data_by_mail(self):
        if settings.SEND_EMAILS:
            message = render_to_string('application/email/data.txt', {'object': self, 'first_name': self.first_name, 'nickname': self.nickname, 'my_referral': self.my_referral,})
            email = EmailMessage(
                subject='OpenCon 2016 Application Received',
                body=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[self.email],
                bcc=settings.EMAIL_DATA_BACKUP,
            )
            email.content_subtype = "html"
            email.send(fail_silently=True)

    def recalculate_ratings(self):
        try:
            rating1 = sum(r.rating for r in self.ratings.all()) / self.ratings.count()
        except ZeroDivisionError:
            rating1 = 0

        try:
            rating2 = sum(r.rating for r in self.ratings2.all()) / self.ratings2.count()
        except ZeroDivisionError:
            rating2 = 0

        self.rating1 = rating1
        self.rating2 = rating2

        # Normally, every application should have a certain number of reviews
        self.need_rating1 = self.ratings.count() < MAX_REVIEWS_ROUND_ONE
        self.need_rating2 = self.ratings2.count() < MAX_REVIEWS_ROUND_TWO

        # However, there are exceptions...
        # If this is a very low quality application
        if self.rating1 <= RATING_R1_LOW_THRESHOLD:
            # And it has exactly 1 review
            if self.ratings.count() == 1:
                # no other reviews are needed (i.e., do not get a second review)
                self.need_rating1 = False

        # Or if the rating is in the middle range <X,Y)
        elif NEEDED_RATING_FOR_THIRD_REVIEW_ROUND1 <= self.rating1 < NEEDED_RATING_TO_ROUND2:
            # And it has exactly 2 reviews
            if self.ratings.count() == 2:
                ratings = list(self.ratings.all())
                r1 = ratings[0].rating
                r2 = ratings[1].rating

                # And the difference between them is big enough
                if abs(r1-r2) > NEEDED_DIFFERENCE_FOR_THIRD_REVIEW_ROUND1:
                    # it needs a 3rd review ("third opinion")
                    self.need_rating1 = True

        if self.status == 'blacklisted':
            self.rating1 = 0
            self.rating2 = 0
            self.need_rating1 = False
            self.need_rating2 = False
        elif self.status == 'whitelist2':
            self.need_rating1 = False
        elif self.status == 'whitelist3':
            self.need_rating1 = False
            self.need_rating2 = False

    rating1 = models.FloatField(default=0)
    rating2 = models.FloatField(default=0)
    need_rating1 = models.BooleanField(default=True)
    need_rating2 = models.BooleanField(default=True)

    def get_rating1(self):
        return round(self.rating1, 1)

    def get_rating2(self):
        return round(self.rating2, 1)

    objects = ApplicationManager()

    def get_data(self, fields=None):
        fields = fields or [x for x in self.__dict__.keys() if not x.startswith('_')]
        data = []
        for field_name in fields:
            current_field = {}
            clean = self._meta.get_field(field_name)
            value = getattr(self, field_name)
            if field_name=='area_of_interest':
                value=''.join([item[1] for item in AREA_OF_INTEREST_CHOICES if item[0] == value])
            if field_name=='experience':
                value=''.join([item[1] for item in EXPERIENCE_CHOICES if item[0] == value])
            if field_name=='fields_of_study':
                value=''.join([item[1] for item in FIELDS_OF_STUDY_CHOICES if item[0] == value])
            if value:
                current_field.update({'title': clean.verbose_name, 'content': value, 'name': field_name})
            if clean.help_text:
                current_field.update({'help': clean.help_text})
            if current_field:
                data.append(current_field)
        return data

    status = models.TextField(choices=STATUS_CHOICES, default=STATUS_CHOICES[0][0])
    status_reason = models.TextField(null=True, blank=True)
    status_by = models.ForeignKey('rating.User', related_name='statuses', null=True, blank=True)
    status_ip = models.GenericIPAddressField(blank=True, null=True)
    status_at = models.DateTimeField(blank=True, null=True)

    def change_status(self, to, by, ip, reason):
        self.status = to
        self.status_by = by
        self.status_ip = ip
        self.status_at = timezone.now()
        self.status_reason = reason
        self.save()


class Reference(TimestampMixin, models.Model):
    key = models.CharField(max_length=settings.MAX_CUSTOM_REFERRAL_LENGTH, unique=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    text = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='organizations/', blank=True, null=True)
    deadline = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return '{1} - {0}'.format(self.name, self.key)
