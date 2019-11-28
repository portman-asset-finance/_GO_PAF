from django.db import models

from core_agreement_crud.models import go_agreement_definitions


class LazyBatchConfig(models.Model):

    SOURCE_CHOICES = (
        ('GO', 'GO'),
        ('SENTINEL', 'SENTINEL')
    )

    PHASE_CHOICES = (
        ('Primary', 'Primary'),
        ('Secondary', 'Secondary')
    )

    batch_name = models.CharField(max_length=50)

    batch_description = models.TextField(null=True)

    agreement_type = models.ForeignKey(go_agreement_definitions, on_delete=models.DO_NOTHING, null=True)

    agreement_phase = models.CharField(max_length=10, choices=PHASE_CHOICES, null=True)

    source_type = models.CharField(max_length=10, choices=SOURCE_CHOICES, null=True)

    run_date = models.DateTimeField(null=True, blank=True)

    last_ran = models.DateTimeField(null=True, blank=True)

    repeat = models.SmallIntegerField(default=1)

    priority = models.SmallIntegerField(unique=True, null=True, blank=True)

    in_progress= models.SmallIntegerField(default=0)

    enabled = models.SmallIntegerField(default=1)

    created = models.DateTimeField(auto_now_add=True)

    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.batch_name


class LazyBatchLog(models.Model):

    LEVEL_CHOICES = (
        ('I', 'Info'),
        ('W', 'Warning'),
        ('E', 'Error')
    )

    batch = models.ForeignKey(LazyBatchConfig, on_delete=models.DO_NOTHING, null=True)

    due_date = models.DateTimeField(null=True, blank=True)

    level = models.CharField(max_length=1, choices=LEVEL_CHOICES, default='I')

    entry = models.TextField(blank=True)

    created = models.DateTimeField(auto_now_add=True)
