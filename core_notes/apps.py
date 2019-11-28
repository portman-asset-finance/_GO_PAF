import os

from django.apps import AppConfig


class NotesConfig(AppConfig):

    name = 'core_notes'

    login_url = 'signin'

    assets_directory = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "core_notes\_assets")
