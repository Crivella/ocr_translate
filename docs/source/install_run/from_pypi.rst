From PyPI installation
----------------------

When installing the project from PyPI, only the app is available.
This will need to be integrated in a Django project in order to be used.
These are the minimal instruction for creating a project and start running the server

- (Optional) create and use a `virtual environment <https://docs.python.org/3/library/venv.html>`_

  - :code:`python -m venv venv`
  - :code:`venv\Scripts\activate`

- :code:`pip install django-ocr_translate`
- :code:`django-admin startproject mysite`
- Configure the server by replacing the automatically created files (strongly recommended):

  - [settings.py](mysite/settings.py) with the one available on the repo.
  - [urls.py](mysite/urls.py) with the one available on the repo.

- or by manually editing the files:

  - settings.py: Add the :code:`ocr_translated` app to the :code:`INSTALLED_APPS`
  - urls.py: Include the :code:`'ocr_translate.urls'` into your project urls.

- From here follow the same instructions as :ref:`with Github <github_run_server>`
