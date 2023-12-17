From PyPI installation
----------------------

See the section on how to :doc:`install from PyPI </install/index>` first.

When installing the project from PyPI, only the app is available.
This will need to be integrated in a Django project in order to be used.
These are the minimal instruction for creating a project and start running the server:

- Run :code:`django-admin startproject mysite` to create a django project
- Configure the server by replacing the automatically created files (strongly recommended):
  - [settings.py](mysite/settings.py) with the one available on the repo.
  - [urls.py](mysite/urls.py) with the one available on the repo.
- or by manually editing the files:
  - settings.py: Add the :code:`ocr_translated` app to the :code:`INSTALLED_APPS`
  - urls.py: Include the :code:`'ocr_translate.urls'` into your project urls.
- From here follow the same instructions as when starting :doc:`from Github </running/from_github>`
