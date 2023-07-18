# OCR_translate

This is a Django app for creating back-end server aimed at performing OCR and translation of images received via a POST request.

The OCR and translation is performed using freely available machine learning models and packages (see below for what is currently implemented).

The server is designed to be used together with [this browser extension](https://github.com/Crivella/ocr_extension), acting as a front-end providing the images and controlling the model languages and models being used.

## Installation

It is strongly suggested to install this project using a [virtual environment](https://docs.python.org/3/library/venv.html).

### From Github

- Clone or download the repository
  - `git clone https://github.com/Crivella/ocr_translate.git`
- Install the project dependencies (choose the appropriate files depending if you wanna run on GPU or CPU only):
  - `pip install -r requirements-torch-[cpu/cuda].txt`
  - `pip install -r requirements.txt`

### From Docker
Plan to add a CPU and a CUDA specific image to DockerHUB.
For now you can create the image yourself by:

- Create a .pip-cache-cpu directory inside your project.
- Optional: re-install the project dependencies pointing this as the cache folder for pip (will make the build process much faster, by reusing the cached dependencies)
- Run `docker build -t ocr_server .`


### From PyPI

Run the command

- `pip install django-ocr_translate`

By default torch 2.x will come in its CUDA enabled version. While this works also for CPU, it will also install ~1 GB of cuda dependencies.
If you wish to run on CPU only, download the file [requirements-torch-cpu.txt](requirements-torch-cpu.txt) first and run

- `pip install -r requirements-torch-cpu.txt`

before installing the python package.

## Running the server

By default the server will use a sqlite database named *db.sqlite3* inside the project main directory.
If you plan to use a different database, you can either:

- manually edit the [settings.py](mysite/settings.py)
- Use the provided [Environment variables](#environment-variables)
See below for a [list of supported databases](#supported-databases)

You will also have to modify the `ALLOWED_HOSTS` in case you plan to access the server from somewhere other than *localhost*.

### From Github installation

The Github repo provides not only the Django app files, but also the already configured project files used to start the server.

Create/Initialize your database by running

- `python manage.py migrate`

inside your project folder.

Run the server using for example one of the following options:

- Django development server. This is more oriented for developing than deploying, but is fine for a self-hosted single-user server accepting connections only on *localhost*
  - From inside the project directory: `python manage.py runserver PORT`
  - The suggested PORT would be 4000 as it is the one set by default in the extension
- [Nginx](https://www.nginx.com/) + [Gunicorn](https://gunicorn.org/):
  - Check the [Dockerfile](Dockerfile), as this is what the provided image makes use of.

At least for the first time, it is suggested to run the server with the [Environment variables](#environment-variables) `AUTOCREATE_LANGUAGES` and `AUTOCREATE_VALIDATED_MODELS` set to `"true"` to automatically load the validated languages and models provided by the project.

Notes:

- Gunicorn workers will each spawn a separate instance of the loaded models, each taking its own space in the memory. This can quickly fill up the memory especially if running on GPU. Ideally set this to 1.
- Django development server will spawn new threads for handling incoming requests (if no currently existing thread is free), which share the same memory. Running more than one worker per loaded model concurrently might slow down the actual computation and in some case also block the execution.

### From PyPI installation

When installing the project from PyPI, only the app is available.
This will need to be integrated in a Django project in order to be used.
These are the minimal instruction for creating a project and start running the server:

- Run `django-admin startproject mysite` to create a django project
- Configure the server by replacing the automatically created files (strongly recommended):
  - [settings.py](mysite/settings.py) with the one available on the repo.
  - [urls.py](mysite/urls.py) with the one available on the repo.
- or by manually editing the files:
  - settings.py: Add the `ocr_translated` app to the `INSTALLED_APPS`
  - urls.py: Include the `'ocr_translate.urls'` into your project urls.
- From here follow the same instructions as when starting [from Github](#from-github)

### From docker

This section assumes you have docker installed and the image of the project.

Run the command:

- `docker run --name CONTAINER_NAME -v PATH_TO_YOUR_MODEL_DIRECTORY:/models -v PATH_TO_DIR_WITH_SQLITE_FILE:/data --env-file=PATH_TO_AND_ENV_VARIABLE_FILE -p SERVER_PORT:4000 -d ocr_server`

See the [Environment variables](#environment-variables) section for configuring your environment variable file. Additionaly the docker image defines 2 other variable to automatically create an admin user for managing the database via the django-admin interface:

- `UID`: UID of the user owning the files in /models and /data
- `GID`: GID of the user owning the files in /models and /data
- `NUM_WEB_WORKERS`: Number of gunicorn workers for the server
- `DJANGO_SUPERUSER_USERNAME`: The username of the admin user to be created.
- `DJANGO_SUPERUSER_PASSWORD`: The password of the admin user to be created.

## Supported Box OCR models

- [EasyOCR](https://github.com/JaidedAI/EasyOCR)

## Supported text OCR models

- Hugging Face [Transformers](https://huggingface.co/docs/transformers/index) VisionEncoderDecoder models
- [Tesseract](https://github.com/tesseract-ocr/tesseract) (Requires tesseract to be [installed on the machine](https://tesseract-ocr.github.io/tessdoc/Installation.html))

## Supported translation models

- Hugging Face [Seq2Seq](https://huggingface.co/learn/nlp-course/chapter1/7) models

## Endpoints

This is not a REST API. As of now the communication between the server and a front-end is stateful and depend on the languages and models currently loaded on the server.
In the future it would be interesting to separate the worker and database server, for an actual deployment, but might make the self-hosting more difficult to manage.

| Endpoint | Method | Usage |
| --- | --- | ---|
| `/` | GET | Handshake: the server will replay with a JSON response containing information about the available languages/models and the currently in use src/dst language and box/ocr/tsl models |
| `/get_trans/` | GET | Request to get all the available translations (e.g. using different models) of the text specified by the `text` GET parameter |
| `/set_lang` | POST | JSON request to switch the currently selected languages to the one specified by the keys: `lang_src`, `lang_dst` |
| `/set_models` | POST | JSON request to switch the currently loaded models to the one specified by the keys: `box_model_id`, `ocr_model_id`, `tsl_model_id` |
| `/run_tsl` | POST | JSON request to run the translation for the text specified by the key `text` |
| `/run_ocrtsl` | POST | JSON request to run the OCR and translation of an image (base64 as the `contents` key) or provide a previously obtained result (md5 of the base64 as the `md5` key). `md5` should be always specified, `contents` is optional |

## Environment variables

The first section of variable is defined at the APP level and will be available both for installation from Github or PyPI.
The second section of variables is defined at the project level and is only available if using the [settings.py](mysite/settings.py) provided in the repo.

### App variables

| Variable | Values | Usage |
| --- | --- | --- |
| `LOAD_ON_START`| false[/true] | Will automatically load the most used source/destination languages and most used models for that language combination at server start|
| `AUTOCREATE_LANGUAGES` | false[/true] | Will automatically create the Language entries in the database as defined in [languages.json](ocr_translate/OCR_TSL/languages.json) |
| `AUTOCREATE_VALIDATED_MODELS` | false[/true] | Will automatically create the model entries that have been tested and defined in [models.json](ocr_translate/OCR_TSL/models.json). NOTE: Creation of the models requires the involved languages to already exist in the database |
| `DEVICE` | cpu[/cuda] | Which device to use with torch |
| `EASYOCR_MODULE_PATH` | `$HOME/.EasyOCR` | Directory where EasyOCR store its downloaded models |
| `TRANSFORMERS_CACHE` | `$HOME/.cache/huggingface/hub/` | Directory where [Hugging Face](https://huggingface.co/) models are being stored (either downloaded manually or downloaded by `transformers`) |
| `TRANSFORMERS_OFFLINE` | 1[/0] | By default `transformers` will try to download missing models. Set this to 0 to only work in offline mode |
| `TESSERACT_PREFIX` | `$TRANSFORMERS_CACHE/tesseract` | Directory where tesseract will store and look for models |
| `TESSERACT_ALLOW_DOWNLOAD` | false[/true] | Control whether the app should download missing models (true) or work in offline mode only (false) |
| `NUM_MAIN_WORKERS` | 4 | Number of `WorkerMessageQueue` workers handling incoming OCR_TSL post requests |
| `NUM_BOX_WORKERS` | 1 | Number of `WorkerMessageQueue` workers handling box_ocr pipelines (Should be set as 1 until the pipeline is build to handle multiple concurrent request efficiently without slowdowns) |
| `NUM_OCR_WORKERS` | 1 | Number of `WorkerMessageQueue` workers handling ocr pipelines (Should be set as 1 until the pipeline is build to handle multiple concurrent request efficiently without slowdowns) |
| `NUM_TSL_WORKERS` | 1 | Number of `WorkerMessageQueue` workers handling translation pipelines (Should be set as 1 until the pipeline is build to handle multiple concurrent request efficiently without slowdowns) |

### Project/server variables

| Variable | Values | Usage |
| ---- | ---- | ---- |
| `DJANGO_DEBUG` | false[/true] | Whether to run the server in debug (true) or production (false) mode |
| `DJANGO_LOG_LEVEL` | INFO | python `logging` level for  |
| `DATABASE_NAME` | *db.sqlite3* | For `sqlite3` this is the path to the database file. For other backend it should be the name of the database |
| `DATABASE_ENGINE` | `django.db.backends.sqlite3` | Change this to either a Django or 3rd party provided backend to use another Database type |
| `DATABASE_HOST` | optional | Required if using another db back-end |
| `DATABASE_PORT` | optional | Required if using another db back-end |
| `DATABASE_USER` | optional | Probably required if using another db back-end |
| `DATABASE_PASSWORD` | optional | Probably required if using another db back-end |

## Supported databases

- [SQLite](https://www.sqlite.org/index.html) This is mostly fine for a self-hosted server accessed by a single  or few users (and it's probably gonna be faster than any other database not running on the same network as the server because of latency).
- [Postgresql](https://www.postgresql.org/)
- [MySQL](https://www.mysql.com)/[MariaDB](https://mariadb.org/)