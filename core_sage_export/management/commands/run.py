from django.core.management.base import BaseCommand

from core_dd_drawdowns.models import BatchHeaders

from core_sage_export.models import SageBatchHeaders, SageBatchTransactions
from core_sage_export.functions import build_sage_transactions_from_batch


class Command(BaseCommand):

    def handle(self, *args, **options):

        SageBatchHeaders.objects.all().delete()
        SageBatchTransactions.objects.all().delete()

        bh_rec = BatchHeaders.objects.get(reference='GO20200307-6895')

        print(build_sage_transactions_from_batch(bh_rec))
