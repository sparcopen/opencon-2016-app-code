import string
import random

from opencon_project.settings.base import *


SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(50))
)

INSTALLED_APPS += [
    'debug_toolbar',
]

# SEND_EMAILS = False
