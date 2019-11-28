from django.core.management.base import BaseCommand

from core_scheduled_tasks import functions
from core_scheduled_tasks.models import GoScheduler, GoSchedulerLog, GoSchedulerConfig

import datetime
import traceback


class Command(BaseCommand):

    active_job = None
    job_begins = None

    def handle(self, *args, **options):

        print('Hello')

        search_criteria = {
            'enabled': 1,
            'in_progress': 0,
            'next_run__lte': datetime.datetime.now()
        }

        # Get jobs that need running.
        jobs_queryset = GoScheduler.objects.filter(**search_criteria).order_by('priority')

        # Log that we are running.
        if not jobs_queryset.exists():
            self.log('I', 'runtasks found 0 jobs. Search criteria: {}'.format(search_criteria))
            return
        else:
            self.log('I', 'runtasks running. {} jobs found. Search criteria: {}'.format(jobs_queryset.count(),
                                                                                        search_criteria))

        for job_qs in jobs_queryset:

            self.active_job = job_qs

            # Update db to say job is in progress (avoid duplicate processing).
            job_qs.in_progress = 1
            job_qs.save()

            self.job_begins = datetime.datetime.now()

            # Write log entry to say job is starting.
            self.log('I', 'Job "{}" starting.'.format(job_qs.task_name))

            # Get job config options / job parameters
            job_params = {}
            job_config_qs = GoSchedulerConfig.objects.filter(go_scheduler=job_qs)
            for param in job_config_qs:
                job_value_type = None
                if getattr(param, 'string'):
                    job_value_type = 'string'
                if getattr(param, 'decimal'):
                    job_value_type = 'decimal'
                if getattr(param, 'integer'):
                    job_value_type = 'integer'
                if getattr(param, 'datetime'):
                    job_value_type = 'datetime'
                if job_value_type:
                    job_params[str(param.task_parameter)] = getattr(param, job_value_type)

            try:
                getattr(functions, job_qs.task_function)(job_qs, job_params)
                self.log('I', 'Job "{}" completed successfully.'.format(job_qs.task_name))
            except Exception as e:

                self.log('E', '{}: {}'.format(e, traceback.format_exc()))

            # Save.
            job_qs.in_progress = 0
            job_qs.last_ran = self.job_begins
            job_qs.save()

        # Log that we are running.
        self.log('I', 'runtasks complete.')

    def log(self, level, message):

        entry_obj = {
            'level': level,
            'entry': '{}'.format(message),
            'job_ran': self.job_begins,
            'go_scheduler': self.active_job
        }

        GoSchedulerLog(**entry_obj).save()
