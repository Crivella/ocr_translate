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


App variable List
-----------------

Variables used by the application.

.. list-table:: Title
    :widths: 25 25 50
    :header-rows: 1

    * - Variable
      - Values
      - Usage
    * - :code:`LOAD_ON_START`
      - false[/true]
      - Will automatically load the most used source/destination languages and most used models for that language combination at server start
    * - :code:`AUTOCREATE_LANGUAGES`
      - false[/true]
      - Will automatically create the Language entries in the database as defined in [languages.json](ocr_translate/OCR_TSL/languages.json)
    * - :code:`AUTOCREATE_VALIDATED_MODELS`
      - false[/true]
      - Will automatically create the model entries defined in code and plugins `entrypoints`.
    * - :code:`DEVICE`
      - cpu[/cuda]
      - Which device to use with torch
    * - :code:`EASYOCR_MODULE_PATH`
      - :code:`$HOME/.EasyOCR`
      - Directory where EasyOCR store its downloaded models
    * - :code:`TRANSFORMERS_CACHE`
      - :code:`$HOME/.cache/huggingface/hub/`
      - Directory where [Hugging Face](https://huggingface.co/) models are being stored (either downloaded manually or downloaded by `transformers`)
    * - :code:`TRANSFORMERS_OFFLINE`
      - 1[/0]
      - By default `transformers` will try to download missing models. Set this to 0 to only work in offline mode
    * - :code:`TESSERACT_PREFIX`
      - :code:`$TRANSFORMERS_CACHE/tesseract`
      - Directory where tesseract will store and look for models
    * - :code:`TESSERACT_ALLOW_DOWNLOAD`
      - false[/true]
      - Control whether the app should download missing models (true) or work in offline mode only (false)
    * - :code:`NUM_MAIN_WORKERS`
      - 4
      - Number of `WorkerMessageQueue` workers handling incoming OCR_TSL post requests
    * - :code:`NUM_BOX_WORKERS`
      - 1
      - Number of `WorkerMessageQueue` workers handling box_ocr pipelines (Should be set as 1 until the pipeline is build to handle multiple concurrent request efficiently without slowdowns)
    * - :code:`NUM_OCR_WORKERS`
      - 1
      - Number of `WorkerMessageQueue` workers handling ocr pipelines (Should be set as 1 until the pipeline is build to handle multiple concurrent request efficiently without slowdowns)
    * - :code:`NUM_TSL_WORKERS`
      - 1
      - Number of `WorkerMessageQueue` workers handling translation pipelines (Should be set as 1 until the pipeline is build to handle multiple concurrent request efficiently without slowdowns)

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
