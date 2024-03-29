"""
Django settings for _go_base project.

Generated by 'django-admin startproject' using Django 2.2.5.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'g0)eb-z_w1yj1-od!@acab9h&!52*z2qsod4i*$201%&k5_(ib'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['apellio-server', 'www.gofintech.co.uk', '127.0.0.1', '10.0.0.69', 'localhost']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'import_export',
    'crispy_forms',
    'django_filters',
    'widget_tweaks',
    'anchorimport.apps.AnchorimportConfig',
    'core.apps.CoreConfig',
    'core_agreement_crud.apps.CoreAgreementCrudConfig',
    'core_direct_debits.apps.CoreDirectDebitsConfig',
    'core_dashboard.apps.DashboardConfig',
    'core_dd_drawdowns.apps.CoreDdDrawdownsConfig',
    'core_dd_datacash.apps.CoreDdDatacashConfig',
    'core_agreement_editor.apps.CoreAgreementEditorConfig',
    'core_sage_export.apps.CoreSageExportConfig',
    'core_notes.apps.NotesConfig',
    'core_bounce.apps.CoreBounceConfig',
    'core_app_ddic.apps.DDICConfig',
    'core_agreement_notice.apps.CoreAgreementNoticeConfig',
    'core_arrears.apps.CoreArrearsConfig',
    'core_payments.apps.CorePaymentsConfig',
    'core_app_worldpay.apps.WorldPayConfig',
    'core_eazycollect.apps.CoreEazycollectConfig',
    'core_lazybatch.apps.CoreLazybatchConfig',
    'core_scheduled_tasks.apps.CoreScheduledTasksConfig',
    'core_companies_house.apps.CoreCompaniesHouseConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = '_go_base.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')]
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = '_go_base.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
#     }
# }
DATABASES = {
    'default': {
        'ENGINE': 'sql_server.pyodbc',
        'NAME': '_GO_PAF_UAT_DB',
        'USER': 'apellioadmin',
        'PASSWORD': 'password',
        'HOST': 'NCFSRV01-MK',
        'OPTIONS': {
            'driver': 'ODBC Driver 13 for SQL Server',
        },
    }
}


# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR,'staticfiles')
STATICFILES_DIRS = (
    os.path.join(BASE_DIR,'static'),
    )
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR,'static','media')

LOGOUT_REDIRECT_URL = '/'
