from django.apps import AppConfig

import os


class CoreBounceConfig(AppConfig):

    name = 'core_bounce'

    datacash_assets_directory = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "core_bounce/_assets/datacash/")
    bacs_assets_directory = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "core_bounce/_assets/bacs/")
