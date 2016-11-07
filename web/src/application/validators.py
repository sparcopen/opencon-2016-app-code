from django.core import validators
from django.core.exceptions import ValidationError
from django.utils.translation import ungettext_lazy

import ast


class MaxChoicesValidator(validators.BaseValidator):
    message = ungettext_lazy(
        'Ensure this value has at most %(limit_value)d choice (it has %(show_value)d).',  # NOQA
        'Ensure this value has at most %(limit_value)d choices (it has %(show_value)d).',  # NOQA
        'limit_value'
    )
    code = 'max_choices'

    def compare(self, a, b):
        return a > b

    def clean(self, x):
        lst = ast.literal_eval(x)
        return len(lst)


class MinChoicesValidator(validators.BaseValidator):
    message = ungettext_lazy(
        'Ensure this value has at least %(limit_value)d choice (it has %(show_value)d).',
        'Ensure this value has at least %(limit_value)d choices (it has %(show_value)d).',
        'limit_value'
    )
    code = 'min_choices'

    def compare(self, a, b):
        return a < b

    def clean(self, x):
        lst = ast.literal_eval(x)
        return len(lst)


class EverythingCheckedValidator(validators.BaseValidator):
    message = ungettext_lazy(
        'Ensure that you checked the choice.',
        'Ensure that you checked all the choices.',
    )
    code = 'everything_checked'

    def compare(self, a, b):
        return a != b

    def clean(self, x):
        lst = ast.literal_eval(x)
        return len(lst)


def none_validator(x):
    x = ast.literal_eval(x)
    if 'none' in x and len(x) > 1:
        raise ValidationError('You cannot choose both "None" and another option.')
