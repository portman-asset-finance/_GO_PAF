from django.core.management.base import BaseCommand, CommandError

from core_scheduled_tasks import functions
from core_scheduled_tasks.models import GoScheduler, GoSchedulerLog, GoSchedulerConfig

import datetime
import traceback


class Command(BaseCommand):

    active_job = None
    job_begins = None

    def handle(self, *args, **options):

        print('Hello')