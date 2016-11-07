from django.core.management.base import BaseCommand, CommandError
from ...models import Application


class Command(BaseCommand):
    help = 'Recalculate ratings for applications'

    def handle(self, *args, **options):
        applications = Application.objects.all()
        app_count = applications.count()

        for i, application in enumerate(applications):
            application.save()
            if i % 20 == 0:
                print('Recalculated: {0:.2f}%'.format(i/app_count*100))

        print('Recalculation done!')
