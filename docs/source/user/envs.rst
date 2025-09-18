Environment Variables
=====================

The server will check a number of environment variables to configure itself.

Setting Environment variables
-----------------------------

Environment variables can be set in many ways depending on the the OS and/or the tool used to launch the server.
This is a list of common possible ways:

- Windows Powershell: :code:`$env:VARIABLE_NAME = "value"` (code must be run in the same shell)
- Windows Command Prompt: :code:`set VARIABLE_NAME=value` (code must be run in the same shell)
  !! Do not use quotes as they will be included in the value
- Windows Settings: :code:`Control Panel > System > Advanced System Settings > Environment Variables`
- Linux BASH: :code:`export VARIABLE_NAME=value` (code must be run in the same shell)
- VSCode: :code:`launch.json > env > VARIABLE_NAME`

.. code-block::

    {
        "version": "0.2.0",
        "configurations": [
            {
                ...
                "env": {
                    "VARIABLE_NAME_1": "VALUE_1",
                    ...
                },
                ...
            }
        ]
    }

- Docker: :code:`docker run -e VARIABLE_NAME=value ...`
- Docker: :code:`docker run --env-file .env ...` where `.env` is a file with the format

.. code-block::

    VARIABLE_NAME_1=VALUE_1
    ...
    VARIABLE_NAME_N=VALUE_N

App variable list
-----------------

Environment variables used by the application.

.. list-table::
  :widths: 20 80
  :header-rows: 1

  * - Variable (=[default])
    - Description
  * - ``AUTOCREATE_LANGUAGES``
      = ``false``
    - Will force the server to automatically create/update the Language entries in the database.
  * - ``DEVICE``
      = ``cpu``
    - Which device to use for plugins that support it. Currently allowed: cpu, cuda
  * - ``LOAD_ON_START``
      = ``false``
    - ``most``: Load the most used models and the respective languages ``last``: Load the last used models and languages source/destination languages and most used models for that language combination at server start
  * - ``NUM_BOX_WORKERS``
      = ``1``
    - Number of ``WorkerMessageQueue`` workers handling box_ocr pipelines (Should be set as 1 until the pipeline is build to handle multiple concurrent request efficiently without slowdowns)
  * - ``NUM_MAIN_WORKERS``
      = ``4``
    - Number of ``WorkerMessageQueue`` workers handling incoming OCR_TSL post requests
  * - ``NUM_OCR_WORKERS``
      = ``1``
    - Number of ``WorkerMessageQueue`` workers handling ocr pipelines (Should be set as 1 until the pipeline is build to handle multiple concurrent request efficiently without slowdowns)
  * - ``NUM_TSL_WORKERS``
      = ``1``
    - Number of ``WorkerMessageQueue`` workers handling translation pipelines (Should be set as 1 until the pipeline is build to handle multiple concurrent request efficiently without slowdowns)
  * - ``OCT_AUTOUPDATE``
      = ``false``
    - If true, the server will attempt to update the main package to the version specified by ``OCT_VERSION``
  * - ``OCT_BASE_DIR``
      = ``false``
    - Path to the base directory of the project. If no other paths are configured using environment variables, the server database, plugin files and downloaded models will be stored here.
  * - ``OCT_VERSION``
      = *OPTIONAL*
    - Default set to the downloaded release version Version the ``run_server.py`` script will attempt to install/update to. Can be either a version number (``A.B.C`` eg ``0.6.1```) or last/latest.

run_server.py variable list
---------------------------

Environment variables used if running the server using the provided `run_server.py` script. This includes the windows release file and docker image that are based on the same script.

.. list-table::
  :widths: 20 80
  :header-rows: 1

  * - Variable (=[default])
    - Description
  * - ``CORS_ALLOWED_ORIGINS``
      = *OPTIONAL*
    - List of semi-colon ``;`` separated URLs that are allowed to access the server. CSRF_TRUSTED_ORIGINS is set to the same value (can use this with USE_CORS_HEADERS=false) to set CSRF_TRUSTED_ORIGINS only. EXAMPLE: ``CORS_ALLOWED_ORIGINS="http://localhost:4000;http://127.0.0.1:4000"``
  * - ``CORS_ALLOW_HEADERS``
      = ``LIB default``
    - List of semi-colon ``;`` separated HTTP headers that are allowed to be used. EXAMPLE: ``CORS_ALLOW_HEADERS="Content-Type;Authorization;X-CSRFToken"``
  * - ``CORS_ALLOW_METHODS``
      = ``LIB default``
    - List of semi-colon ``;`` separated HTTP methods that are allowed to be used. EXAMPLE: ``CORS_ALLOW_METHODS="GET;POST;PUT;DELETE;OPTIONS;PATCH"``
  * - ``DJANGO_SUPERUSER_PASSWORD``
      = ``password``
    - Password for the superuser to be created
  * - ``DJANGO_SUPERUSER_USERNAME``
      = ``admin``
    - Username for the superuser to be created
  * - ``OCT_DJANGO_BIND_ADDRESS``
      = ``127.0.0.1``
    - Address to bind the server to
  * - ``OCT_DJANGO_PORT``
      = ``4000``
    - Port the server will listen to
  * - ``OCT_GUNICORN_NUM_WORKERS``
      = ``1``
    - Number of gunicorn workers
  * - ``OCT_GUNICORN_TIMEOUT``
      = ``1200``
    - Timeout for gunicorn workers
  * - ``OCT_GUNICORN_USER``
      = ``current user``
    - User to run the server as if using gunicorn.
  * - ``USE_CORS_HEADERS``
      = ``false``
    - Allow setting of CORS headers in the server responses

Server variable list
--------------------

Environment variables used specifically by the DJANGO server.

.. list-table::
  :widths: 20 80
  :header-rows: 1

  * - Variable (=[default])
    - Description
  * - ``DATABASE_ENGINE``
      = ``django.db.backends.sqlite3``
    - Change this to either a Django or 3rd party provided backend to use another Database type
  * - ``DATABASE_HOST``
      = ``optional``
    - Required if using another database backend
  * - ``DATABASE_NAME``
      = ``db.sqlite3``
    - For ``sqlite3`` this is the path to the database file. For other backends, it should be the name of the database
  * - ``DATABASE_PASSWORD``
      = ``optional``
    - Probably required if using another database backend
  * - ``DATABASE_PORT``
      = ``optional``
    - Required if using another database backend
  * - ``DATABASE_USER``
      = ``optional``
    - Probably required if using another database backend
  * - ``DJANGO_ALLOWED_HOSTS``
      = ``optional``
    - Add list of semi-colon ``;`` separated IPs to the ``ALLOWED_HOSTS`` of the server. Needed if you want to host the server on a different machine than the one querying it. EXAMPLE: ``DJANGO_ALLOWED_HOSTS="192.168.1.1;172.108.104.3"``. See Django Documentation for more info: https://docs.djangoproject.com/en/2.2/ref/settings/#allowed-hosts
  * - ``DJANGO_DEBUG``
      = ``false``
    - Whether to run the server in debug (true) or production (false) mode
  * - ``DJANGO_LOG_LEVEL``
      = ``INFO``
    - Python ``logging`` level. See https://docs.python.org/3/library/logging.html#logging-levels for allowed values


Plugin specific variables
-------------------------

See :doc:`plugins doc <../plugins/index>`

Docker exceptions
-------------------------

In Docker environments, the values of :code:`OCT_DJANGO_PORT` and :code:`OCT_BASE_DIR` are overridden and cannot be customized.

To persist data, bind mount the container path :code:`/plugin_data`. The server listens on port :code:`4000`, which should be mapped to the desired host port.


.. _logging_docs: https://docs.python.org/3/library/logging.html#logging-levels
