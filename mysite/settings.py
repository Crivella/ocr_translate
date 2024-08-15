###################################################################################
# ocr_translate - a django app to perform OCR and translation of images.          #
# Copyright (C) 2023-present Davide Grassano                                      #
#                                                                                 #
# This program is free software: you can redistribute it and/or modify            #
# it under the terms of the GNU General Public License as published by            #
# the Free Software Foundation, either version 3 of the License.                  #
#                                                                                 #
# This program is distributed in the hope that it will be useful,                 #
# but WITHOUT ANY WARRANTY; without even the implied warranty of                  #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                   #
# GNU General Public License for more details.                                    #
#                                                                                 #
# You should have received a copy of the GNU General Public License               #
# along with this program.  If not, see {http://www.gnu.org/licenses/}.           #
#                                                                                 #
# Home: https://github.com/Crivella/ocr_translate                                 #
###################################################################################
"""
Django settings for ocr_translate project.

Generated by 'django-admin startproject' using Django 4.2.2.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

import os
from pathlib import Path

from ocr_translate.plugin_manager import PluginManager

PMNG = PluginManager()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} - {asctime} - {module} - {process:d} - {thread:d} - {message}',
            'style': '{',
            },
        'medium': {
            'format': '{asctime} - {levelname:>7s} - {name:>15s}:{module:<15s} - {message}',
            'style': '{',
            },
        'simple': {
            'format': '{levelname} - {message}',
            'style': '{',
            },
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': os.environ.get('DJANGO_LOG_LEVEL', 'INFO'),
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'medium',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'ocr.general': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'propagate': False,
        },
        'ocr.worker': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'propagate': False,
        },
        'plugin': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'propagate': False,
        },
    },
}


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-7h+*^e963rdi*2jbdlhqvmg%xnx$9@s*ccgcfae@t219$#!)vu')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DJANGO_DEBUG', '').lower() == 'true'

ALLOWED_HOSTS = ['localhost', '127.0.0.1']
ALLOWED_HOSTS += os.environ.get('DJANGO_ALLOWED_HOSTS', '').split(';')


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'ocr_translate',
] + PMNG.plugins

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'mysite.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'mysite.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASE_ENGINE = os.environ.get('DATABASE_ENGINE', 'django.db.backends.sqlite3')
DATABASE_NAME = os.environ.get('DATABASE_NAME', os.path.join(BASE_DIR, 'db.sqlite3'))

DATABASE = {
    'ENGINE': DATABASE_ENGINE,
    'NAME': DATABASE_NAME,
}

for k in ['USER', 'PASSWORD', 'HOST', 'PORT']:
    if not os.environ.get('DATABASE_' + k) is None:
        DATABASE[k] = os.environ.get('DATABASE_' + k)

OPTIONS = {}
if DATABASE_ENGINE == 'django.db.backends.mysql':
    # https://stackoverflow.com/questions/2108824/mysql-incorrect-string-value-error-when-save-unicode-string-in-django
    OPTIONS['charset'] = 'utf8mb4'

if DATABASE_ENGINE == 'django.db.backends.sqlite3':
    ptr = {}
    DATABASE['OPTIONS'] = ptr
    ptr['init_command'] = 'PRAGMA journal_mode=wal;'

DATABASES = {
    'default': DATABASE
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True




# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
DATA_UPLOAD_MAX_MEMORY_SIZE = 10*1024*1024

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

# STATIC_URL = 'static/'

STATIC_URL = '/static/'

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
    )
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
