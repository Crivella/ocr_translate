Project variable list
---------------------

List of environment variables used in this project to configure the application behavior.

.. list-table::
  :widths: 20 80
  :header-rows: 1

  * - Variable (=[default])
    - Description
  * - ``COLUMNS``

      = *OPTIONAL*
    - Number of columns the rich logging should use if enabled. Particularly useful in docker environments if the terminal width is not detected properly.
  * - ``CORS_ALLOWED_ORIGINS``

      = *OPTIONAL*
    - List of semi-colon ``;`` separated URLs that are allowed to access the server. CSRF_TRUSTED_ORIGINS is set to the same value (can use this with USE_CORS_HEADERS=false) to set CSRF_TRUSTED_ORIGINS only. EXAMPLE: ``CORS_ALLOWED_ORIGINS="http://localhost:4000;http://127.0.0.1:4000"``
  * - ``CORS_ALLOW_HEADERS``

      = ``LIB default``
    - List of semi-colon ``;`` separated HTTP headers that are allowed to be used. EXAMPLE: ``CORS_ALLOW_HEADERS="Content-Type;Authorization;X-CSRFToken"``
  * - ``CORS_ALLOW_METHODS``

      = ``LIB default``
    - List of semi-colon ``;`` separated HTTP methods that are allowed to be used. EXAMPLE: ``CORS_ALLOW_METHODS="GET;POST;PUT;DELETE;OPTIONS;PATCH"``
  * - ``DATABASE_ENGINE``

      = ``django.db.backends.sqlite3``
    - Change this to either a Django or 3rd party provided backend to use another Database type
  * - ``DATABASE_HOST``

      = *OPTIONAL*
    - Required if using another database backend
  * - ``DATABASE_NAME``

      = ``db.sqlite3``
    - For ``sqlite3`` this is the path to the database file. For other backends, it should be the name of the database
  * - ``DATABASE_PASSWORD``

      = *OPTIONAL*
    - Probably required if using another database backend
  * - ``DATABASE_PORT``

      = *OPTIONAL*
    - Required if using another database backend
  * - ``DATABASE_USER``

      = *OPTIONAL*
    - Probably required if using another database backend
  * - ``DEVICE``

      = ``cpu``
    - Which device to use for plugins that support it. Currently allowed: cpu, cuda
  * - ``DJANGO_ALLOWED_HOSTS``

      = *OPTIONAL*
    - Add list of semi-colon ``;`` separated IPs to the ``ALLOWED_HOSTS`` of the server. Needed if you want to host the server on a different machine than the one querying it. EXAMPLE: ``DJANGO_ALLOWED_HOSTS="192.168.1.1;172.108.104.3"``. See Django Documentation for more info: https://docs.djangoproject.com/en/2.2/ref/settings/#allowed-hosts
  * - ``DJANGO_DEBUG``

      = ``false``
    - Whether to run the server in debug (true) or production (false) mode
  * - ``DJANGO_LOG_LEVEL``

      = ``INFO``
    - Python ``logging`` level. See https://docs.python.org/3/library/logging.html#logging-levels for allowed values
  * - ``DJANGO_SUPERUSER_PASSWORD``

      = ``password``
    - Password for the superuser to be created
  * - ``DJANGO_SUPERUSER_USERNAME``

      = ``admin``
    - Username for the superuser to be created
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
  * - ``OCT_DISABLE_PLUGINS``

      = ``false``
    - If true, all plugins will be disabled and not loaded at server start. Mostly used for testing purposes.
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
  * - ``OCT_LOGFILE``

      = ``false``
    - true/false/path. If true, a logfile named ``ocr_translate.log`` will be created in the base directory. If a path is provided, that will be used instead.
  * - ``OCT_PKG_<NAME>_<VAR>``

      = *OPTIONAL*
    - <NAME> = [the package name]  <VAR> = [VERSION|SCOPE|EXTRAS]. Override the version, scope or extras of a package to be installed/updated. EXAMPLE: ``OCT_PKG_TORCH_VERSION="A.B.C"``. If the package name contains a ``-`` it should be replaced with ``_min_`` in the package name.
  * - ``OCT_VERSION``

      = *OPTIONAL*
    - Default set to the downloaded release version Version the ``run_server.py`` script will attempt to install/update to. Can be either a version number (``A.B.C`` eg ``0.6.1```) or last/latest.
  * - ``USE_CORS_HEADERS``

      = ``false``
    - Allow setting of CORS headers in the server responses

Plugin variable list
--------------------

List of environment variables used by various plugins to configure their behavior. For more details visit the respective plugin documentation.

.. list-table::
  :widths: 20 80
  :header-rows: 1

  * - Variable (=[default])
    - Description
  * - ``EASYOCR_MODULE_PATH``

      = ``<OCT_BASE_DIR>/models/easyocr``
    - Path to a directory where easyocr models will be downloaded and loaded from.
  * - ``OCT_OLLAMA_ENDPOINT``

      = *REQUIRED*
    - Endpoint URL for the Ollama API.
  * - ``OCT_OLLAMA_PREFIX``

      = ``oct_ollama``
    - Prefix added to the model name, made customizable via environment variable since people might not want to setup a dedicated server for this.
  * - ``PADDLEOCR_PREFIX``

      = ``<OCT_BASE_DIR>/models/paddleocr``
    - Path to a directory where paddleocr models will be downloaded and loaded from.
  * - ``TESSERACT_ALLOW_DOWNLOAD``

      = ``true``
    - If true, tesseract will attempt to download missing language models when needed.
  * - ``TESSERACT_PREFIX``

      = *OPTIONAL*
    - Path to a directory where tesseract  models will be downloaded and loaded from.
  * - ``TRANSFORMERS_CACHE``

      = ``<OCT_BASE_DIR>/models/transformers``
    - Path to a directory where transformers models will be downloaded and loaded from.
  * - ``TRANSFORMERS_OFFLINE``

      = ``0``
    - If set to 1, transformers will not attempt to download models and will only use models already present in the storage cache.

Utility run scripts
-------------------

List of environment variables used in the ``run/run-user.[sh|bat]`` scripts to configure their behavior.

.. list-table::
  :widths: 20 80
  :header-rows: 1

  * - Variable (=[default])
    - Description
  * - ``PIP_INSTALLER_LOCATION``

      = *OPTIONAL*
    - Path to a pip installer script like ``get-pip.py`` to allow python to bootstrap pip if it is not available in the current python environment.
  * - ``PYTHON``

      = ``python``
    - Python executable to use to run the script. Mostly used to choose the initial version with which to create the virtual environment.
  * - ``SKIP_VENV``

      = ``false``
    - If true, the script will not attempt to create/use a virtual environment and will run using the current python environment.
  * - ``VENV_DIR``

      = ``<CURRENT_DIR>/venv``
    - Path to the virtual environment directory to use/create.

Docker environment variables
----------------------------

List of environment variables used by the ``start-server.sh`` in docker.

.. list-table::
  :widths: 20 80
  :header-rows: 1

  * - Variable (=[default])
    - Description
  * - ``GID``

      = ``1000``
    - Group ID to run the server as inside the container. Mostly useful when mounting volumes to avoid permission issues.
  * - ``UID``

      = ``1000``
    - User ID to run the server as inside the container. Mostly useful when mounting volumes to avoid permission issues.
