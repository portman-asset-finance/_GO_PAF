from django.core.management.base import BaseCommand

from core_dd_drawdowns.models import Log


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('log_ids', nargs='+', type=int)

    def handle(self, *args, **options):
        for log_id in options['log_ids']:
            try:
                log_rec = Log.objects.get(id=log_id)
            except:
                print('Log ID {} does not exist.'.format(log_rec))
                continue


