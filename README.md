<div align="center">
  <p align="center">
	<a href="https://pypi.org/project/django-ocr_translate/"><img src="https://img.shields.io/pypi/dm/django-ocr_translate?style=flat-square" alt="pypi"/></a>
	<a href="https://pypi.org/project/django-ocr_translate/"><img src="https://img.shields.io/pypi/v/django-ocr_translate?style=flat-square" /></a>
	<a href="https://pypi.org/project/django-ocr_translate/"><img src="https://img.shields.io/github/downloads/Crivella/ocr_translate/total.svg?style=flat-square" /></a>
  <br />
	<a href="https://crivella.github.io/ocr_translate/"><img src="https://img.shields.io/badge/GitHub%20Pages-222222?style=for-the-badge&logo=GitHub%20Pages&logoColor=white" alt="pypi"/></a>
  </p>
</div>

# OCR_translate

This is a Django app for creating back-end server aimed at performing OCR and translation of images received via a POST request.

The OCR and translation is performed using freely available machine learning models and packages (see below for what is currently implemented).

The server is designed to be used together with [this browser extension](https://github.com/Crivella/ocr_extension), acting as a front-end providing the images and controlling the languages, models and plugins being used.

For more information, please consult the **[Full Documentation](https://crivella.github.io/ocr_translate/)**

## Plugins

The server is designed to only offer the basic functionalities, while the models that can be used and how they are used are defined by plugins.

See the documentation for a [list of available plugins](https://crivella.github.io/ocr_translate/user/index.html#known-validated-plugins)

<!-- - [ocr_translate-hugging_face](https://github.com/Crivella/ocr_translate-hugging_face): Plugin for using Hugging Face models for OCR and translation.
- [ocr_translate-easyocr](https://github.com/Crivella/ocr_translate-easyocr): Plugin for using EasyOCR models for BBox detection.
- [ocr_translate-tesseract](https://github.com/Crivella/ocr_translate-tesseract): Plugin for using Tesseract models for OCR.
- [ocr_translate-paddle](https://github.com/Crivella/ocr_translate-paddle): Plugin for using PaddleOCR models for BBox detection and OCR.
- [ocr_translate-ollama](https://github.com/Crivella/ocr_translate-ollama): Plugin for using LLMs through ollama for translation.
- [ocr_translate-google](https://github.com/Crivella/ocr_translate-google): Plugin for using Google Translate for translation. -->


## Running the server

${\color{red}{\bf !!!!}}$ Since version `v0.6` (all methods but the docker image), `python` (or at least) `pip` needs to be installed on the system. (See https://www.python.org/downloads/)

All the different way to run the server may provide different set of default values (each of them is targeted for a different level of usage).

**NOTE**: For all of the following methods, the behavior of the server (eg: model/plugin/db install locations nd allowed hosts) can be customized using [Environment variables](https://crivella.github.io/ocr_translate/user/envs.html)

### From Release file (Windows)

(Tested on Windows 11)

- Make sure to have [python](https://www.python.org/downloads/windows/) (3.11 suggested) installed on your system and available in the PATH (There is a checkbox as soon as you run the installer to automatically do this).
- Download the [release file](/../../releases/latest/download/run_server.zip)
- Unzip the file
- Run the `run_server.exe` file

The server will run with sensible defaults. Most notably the models files, plugin files (needed python packages) and database will be downloaded/created under `%userprofile%/.ocr_translate`.

### From Github

${\color{red}{\bf !!!!}}$ This assumes you have access to a terminal and have `python` and `git` installed on your system.

The Github repo provides not only the Django app files, but also the already configured project files used to start the server.

- Clone or download the repository

      git clone https://github.com/Crivella/ocr_translate.git
      cd ocr_translate

- Install the project and its dependencies

      pip install .

Run the server by using the provided [run_server.py](run_server.py) script.

    python run_server.py

By default the Django development server will be used. You can install [gunicorn](https://gunicorn.org/)

    pip install gunicorn

and the script will use it instead.

${\color{red}{\bf !!!!}}$ Gunicorn will work on UNIX system only ([see missing module fcntl](https://stackoverflow.com/questions/62788628/modulenotfounderror-no-module-named-fcntl))

### Notes

- Gunicorn workers will each spawn a separate instance of the loaded models, each taking its own space in the memory. This can quickly fill up the memory especially if running on GPU. Ideally set this to 1.
- Django development server will spawn new threads for handling incoming requests (if no currently existing thread is free), which share the same memory. Running more than one worker per loaded model concurrently might slow down the actual computation and in some case also block the execution.

### From PyPI installation

Run the command

    pip install django-ocr_translate

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

### From docker image

This section assumes you have docker installed!!!

Images are available on [DockerHUB](https://hub.docker.com/r/crivella1/ocr_translate):

Download the image from DockerHUB:

    docker pull crivella1/ocr_translate:latest

or create it manually create your image:

    docker build -t IMAGE_TAG -f Dockerfile

Run the container by tuning the following command:

    docker run --name CONTAINER_NAME -v OCT_MODELS:/models -v OCT_DB_DATA:/db_data -v OCT_PLUGINS_DATA:/plugins_data -p SERVER_PORT:4000 -d IMAGE_NAME

Replace the all caps parts with the appropriate values.
For the volumes you can either specify a native docker volume using a name or a bind mount using a path (see [docker documentation](https://docs.docker.com/storage/volumes/)).
While it is possible to omit the `-v` this will result in a new volume with random name being created each time the container is run, making it hard to reuse previous data.

- `UID`: UID of the user owning the files in /models, /db_data and /plugin_data
- `GID`: GID of the user owning the files in /models, /db_data and /plugin_data

### SuperUser

Following the described procedures, the server will be created with a admin user *admin*:*password*.

You can login to the admin interface at `http://127.0.0.1:4000/admin/` in order to manage the database.
The main idea is to use this to manually add new models (with the appropriate entrypoint) if you want to test out,
model that are not yet available. (If you find good models, please do share).

${\color{red}{\bf !!!!}}$ The server by default is open only to localhost. If you ever plan to change this, make sure to change the admin password (or even create a new admin user and delete the default one).

## GPU

By default the [run_server.py](run_server.py) will attempt to use a specific device following:

- If the environment variable `DEVICE` is set, it will use the device specified by the value.
- If `torch` is already installed it will be used to determine the device (cpu/cuda).
- If `nvidia-smi` is available the server will try running in GPU mode.
- If none of the above is available, the server will run in CPU mode.

As of `v0.6` no device specific dependencies are included by default, but some plugins will install/use different dependencies based on the device used.

## Possible problems

- [Issue 25](/../../issues/25) Using uBlock origin (or possibly other extension capable of blocking content) could stop the extension from sending requests to the server. This can be recognized if the popup for setting the language and models works fine but than the translations fails without producing any new log in the server windows. (WIP long term fix in the extension)

- [Issue 27](/../../issues/27) Having non latin characters in the model's path can cause HuggingFace `transformers` to fail loading them
