import csv

from django.core.management.base import BaseCommand, CommandError
from ...models import User


class Command(BaseCommand):
    help = 'Add users to database from /data/user_list.txt'

    def handle(self, *args, **options):
        with open('data/user_list.txt') as file:
            reader = csv.reader(file, delimiter=',', quotechar='"')
            header=next(reader, None)
            # print('Deleting old users...')
            # User.objects.all().delete()
            for row in reader:
                email=row[0]
                first_name=row[1]
                last_name=row[2]
                nick=row[3]
                try:
                    user, created = User.objects.get_or_create(email=email, first_name=first_name, last_name=last_name, nick=nick)
                    if created:
                        user.save()
                except:
                    print('Failed to import ' + email)
