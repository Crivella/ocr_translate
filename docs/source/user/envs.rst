Environment Variables
=====================

The server will check a number of environment variables to configure itself.

Setting Environment variables
-----------------------------

Environment variables can be set in many ways depending on the the OS and/or the tool used to launch the server.
This is a list of common possible ways:

- Windows Powershell: :code:`$env:VARIABLE_NAME = "value"` (code must be run in the same shell)
- Windows Command Prompt: :code:`set VARIABLE_NAME=value` (code must be run in the same shell)
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

App variable List
-----------------

Variables used by the application.

.. list-table:: Title
    :widths: 16 16 68
    :header-rows: 1

    * - Variable
      - Default
      - Usage
    * - :code:`OCT_BASE_DIR`
      - false
      - Path to the base directory of the project.

        If no other paths are configured using environment

        variables, the server database, plugin files

        and downloaded models will be stored here.
    * - :code:`LOAD_ON_START`
      - false
      - Will automatically load the most used

        source/destination languages and most used models

        for that language combination at server start
    * - :code:`AUTOCREATE_LANGUAGES`
      - false
      - Will force the server to automatically

        create/update the Language entries in the database.
    * - :code:`DEVICE`
      - cpu
      - Which device to use for plugins that support it.

        Currently allowed: cpu, cuda
    * - :code:`NUM_MAIN_WORKERS`
      - 4
      - Number of `WorkerMessageQueue` workers handling

        incoming OCR_TSL post requests
    * - :code:`NUM_BOX_WORKERS`
      - 1
      - Number of `WorkerMessageQueue` workers handling

        box_ocr pipelines (Should be set as 1 until the

        pipeline is build to handle multiple concurrent

        request efficiently without slowdowns)
    * - :code:`NUM_OCR_WORKERS`
      - 1
      - Number of `WorkerMessageQueue` workers handling

        ocr pipelines (Should be set as 1 until the

        pipeline is build to handle multiple concurrent

        request efficiently without slowdowns)
    * - :code:`NUM_TSL_WORKERS`
      - 1
      - Number of `WorkerMessageQueue` workers handling

        translation pipelines (Should be set as 1 until

        the pipeline is build to handle multiple

        concurrent request efficiently without slowdowns)

run_server.py variable List
---------------------------

This variables are used if running the server using the provided `run_server.py` script.
This includes the windows release file and docker image that are based on the same script.

.. list-table:: Title
    :widths: 16 16 68
    :header-rows: 1

    * - Variable
      - Values
      - Usage
    * - :code:`DJANGO_SUPERUSER_USERNAME`
      - admin
      - Username for the superuser to be created
    * - :code:`DJANGO_SUPERUSER_PASSWORD`
      - password
      - Password for the superuser to be created
    * - :code:`OCT_DJANGO_BIND_ADDRESS`
      - 127.0.0.1
      - Address to bind the server to
    * - :code:`OCT_DJANGO_PORT`
      - 4000
      - Port the server will listen to
    * - :code:`OCT_GUNICORN_USER`
      - current user
      - User to run the server as if using gunicorn.
    * - :code:`OCT_GUNICORN_TIMEOUT`
      - 1200
      - Timeout for gunicorn workers
    * - :code:`OCT_GUNICORN_NUM_WORKERS`
      - 1
      - Number of gunicorn workers

Plugin specific variables
-------------------------

See :doc:`plugins doc <plugins>`

Server variable List
--------------------

Variables used specifically by the DJANGO server.

.. list-table:: Title
    :widths: 25 25 50
    :header-rows: 1

    * - Variable
      - Values
      - Usage
    * - :code:`DJANGO_DEBUG`
      - false[/true]
      - Whether to run the server in debug (true) or production (false) mode
    * - :code:`DJANGO_LOG_LEVEL`
      - INFO
      - python `logging` level for
    * - :code:`DATABASE_NAME`
      - *db.sqlite3*
      - For `sqlite3` this is the path to the database file. For other backend it should be the name of the database
    * - :code:`DATABASE_ENGINE`
      - `django.db.backends.sqlite3`
      - Change this to either a Django or 3rd party provided backend to use another Database type
    * - :code:`DATABASE_HOST`
      - optional
      - Required if using another db back-end
    * - :code:`DATABASE_PORT`
      - optional
      - Required if using another db back-end
    * - :code:`DATABASE_USER`
      - optional
      - Probably required if using another db back-end
    * - :code:`DATABASE_PASSWORD`
      - optional
      - Probably required if using another db back-end
