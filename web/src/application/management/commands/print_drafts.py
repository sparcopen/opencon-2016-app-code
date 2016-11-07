import ast

from django.core.management.base import BaseCommand, CommandError
from ...models import Draft

class Command(BaseCommand):
    help = 'Prints drafts to STDOUT. Usage: python3 manage.py print_drafts > drafts_export.tsv'

    def handle(self, *args, **options):
        fields="""email first_name last_name nickname alternate_email twitter_username institution organization area_of_interest description interested
            goal participation participation_text citizenship residence gender_0 gender_1 occupation degree experience fields_of_study skills_0 skills_1
            how_did_you_find_out_0 how_did_you_find_out_1 scholarship expenses location airport additional_info opt_outs acknowledgements referred_by""".strip().split()
        drafts = Draft.objects.all()
        print('uuid\t', end='')
        for field in fields:
            print(field + '\t', end='')
        print('')
        for draft in drafts:
            uuid=draft.uuid
            data=ast.literal_eval(draft.data)
            print(str(draft.uuid) + '\t', end='')
            for field in fields:
                value=str(data.get(field, "['*NONEXISTENT*']"))
                print(value + '\t', end='')
            print('')
