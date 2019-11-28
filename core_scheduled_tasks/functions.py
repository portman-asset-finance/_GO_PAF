
from datetime import datetime, timedelta

#####################
#                   #
# FUNCTION SKELETON #
#                   #
#####################
#
# def function_name_as_in_go_scheduler_table(job_qs, job_parameters):
#
#     # Step 1: Import any function-specific modules
#     # --------------------------------------------
#     from a_module import a_function
#
#     # Step 2: Execute your function
#     # -----------------------------
#     a_function.a_task(**job_parameters)
#
#     # Step 3: Check the next run date
#     # -------------------------------
#     job_qs.next_run = job_qs.next_run + timedelta(days=1)
#     job_qs.save()
#
#

# * EXISTING FUNCTIONS BELOW DO NOT WORK WITHOUT DEPENDENCIES NOT PROVIDED AS PART OF THE WORK PACKAGE*

def lazybatch(job_qs, job_params):

    from core_lazybatch.functions import create_batches

    # Step 1: Create batches.
    # =======================
    create_batches(**job_params)

    # Step 2: Change next run date to tomorrow.
    # =========================================
    job_qs.next_run = datetime.now() + timedelta(days=1)
    job_qs.save()


def sagewisdom(job_qs, job_params):

    from core_sage_export.models import SageBatchHeaders
    from core_sage_export.functions import build_sage_transactions_from_batch

    # Step 1: Pull in unprocessed Sage Batch Headers
    # ==============================================
    sb_recs = SageBatchHeaders.objects.filter(processed__isnull=True)

    # Step 2: Process.
    # ================
    for sb_rec in sb_recs:
        if sb_rec.batch_header:
            build_sage_transactions_from_batch(sb_rec)

    # Step 3: Change next run date to tomorrow.
    # =========================================
    # job_qs.next_run = job_qs.next_run + timedelta(minutes=10)
    # job_qs.save()


def companyinspector(job_qs, job_params):

    from core_companies_house.functions import Compare_Company_House_Data

    # Step 1: Company information.
    # ============================
    Compare_Company_House_Data(**job_params)

    # Step 2: Change next run date to an hour.
    # ========================================
    job_qs.next_run = datetime.now() + timedelta(days=1)
    job_qs.save()
