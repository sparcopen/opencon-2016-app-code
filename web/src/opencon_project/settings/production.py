from opencon_project.settings.base import *

DEBUG = False
ALLOWED_HOSTS = ['.opencon2016.org'] # production domain
SECRET_KEY = os.environ.get('SECRET_KEY')
