from django.db import models

from core_agreement_crud.models import go_agreement_definitions


class GoScheduler(models.Model):

    task_name = models.CharField(max_length=100)

    task_description = models.TextField()

    task_function = models.CharField(max_length=100)

    next_run = models.DateTimeField(null=True, blank=True)

    last_ran = models.DateTimeField(null=True, blank=True)

    log_file = models.CharField(max_length=250, null=True, blank=True)

    priority = models.SmallIntegerField(unique=True, null=True, blank=True)

    in_progress = models.SmallIntegerField(default=0)

    enabled = models.SmallIntegerField(default=1)

    created = models.DateTimeField(auto_now_add=True)

    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.task_name


class GoSchedulerConfig(models.Model):

    go_scheduler = models.ForeignKey(GoScheduler, on_delete=models.CASCADE, null=True)

    description = models.TextField(null=True)

    task_parameter = models.CharField(max_length=100)

    string = models.TextField(null=True, blank=True)

    decimal = models.DecimalField(null=True, decimal_places=2, max_digits=15, blank=True)

    integer = models.BigIntegerField(null=True, blank=True)

    datetime = models.DateTimeField(null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True)

    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '{}: {}'.format(self.go_scheduler.task_name, self.task_parameter)


class GoSchedulerLog(models.Model):

    LEVEL_CHOICES = (
        ('I', 'Info'),
        ('W', 'Warning'),
        ('E', 'Error')
    )

    go_scheduler = models.ForeignKey(GoScheduler, on_delete=models.CASCADE, null=True)

    level = models.CharField(max_length=1, choices=LEVEL_CHOICES, default='I')

    entry = models.TextField(blank=True)

    job_ran = models.DateTimeField(null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True)
