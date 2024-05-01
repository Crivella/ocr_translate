# OCR_translate

This is a Django app for creating back-end server aimed at performing OCR and translation of images received via a POST request.

The OCR and translation is performed using freely available machine learning models and packages (see below for what is currently implemented).

The server is designed to be used together with [this browser extension](https://github.com/Crivella/ocr_extension), acting as a front-end providing the images and controlling the model languages and models being used.

For more information, please consult the **[Full Documentation](https://crivella.github.io/ocr_translate/)**

## Possible problems

- [Issue 25](#25) Using uBlock origin (or possibly other extension capable of blocking content) could stop the extension from sending requests to the server. This can be recognized if the popup for setting the language and models works fine but than the translations fails without producing any new log in the server windows. (WIP long term fix in the extension)

- [Issue 27](#27) Having non latin characters in the model's path can cause HuggingFace `transformers` to fail loading them

## Running the server

If you plan to use a different settings (eg. database, or model location), you can either:

- manually edit the [settings.py](mysite/settings.py)
- Use the provided [Environment variables](#environment-variables)
See below for a [list of supported databases](#supported-databases)

You will also have to modify the `ALLOWED_HOSTS` in case you plan to access the server from somewhere other than *localhost*.

All the different way to run the server may provide different set of default values (each of them is targeted for a different level of usage).

### From Release file (Windows)

(Tested on Windows 11)
From the [github releases page](/../../releases/) you can download either:

- The [CPU only version](/../../releases/latest/download/run_server-cpu.zip)
- The GPU version split in [file 1](/../../releases/latest/download/run_server-gpu.zip.001) and [file 2](/../../releases/latest/download/run_server-gpu.zip.002) (The CUDA dependencies makes it take much more space), which can be restored using tools like [7zip](https://www.7-zip.org/https://www.7-zip.org/) and [NanaZip](https://github.com/M2Team/NanaZip).

Usage:
Unzip the file and from inside the folder, run the `run_server-XXX.exe` file (XXX=cpu/gpu)

The server will run with sensible defaults. Most notably the models files and database will be downloaded/created under `%userprofile%/.ocr_translate`.
Also the gpu version will attempt to run on GPU by default, and fall-back to CPU if the former is not available.

For customization, you can set the [environment variable](#environment-variables) yourself:

- Windows: either via powershell or by searching for *environment variable* in the settings menu.

**SuperUser**: By default the server will be created with a admin user *admin*:*password* (release only).
You can login to the admin interface at `http://127.0.0.1:4000/admin/` in order to manage the database.
The main idea is to use this to manually add new models (with the appropriate entrypoint) if you want to test out,
model that are not yet available. (If you find good models, please do share).

**NOTE**: The server by default is open only to localhost. If you ever plan to change this, make sure to change the admin password.

### From Github

The Github repo provides not only the Django app files, but also the already configured project files used to start the server.

- Clone or download the repository

      git clone https://github.com/Crivella/ocr_translate.git

- Install the project dependencies (choose the appropriate files depending if you wanna run on GPU or CPU only):

      pip install -r requirements-torch-[cpu/cuda].txt
      pip install -r requirements.txt

Create/Initialize your database by running

    python manage.py migrate

inside your project folder.

**NOTE**: From version 0.3.X model installation and functionalities have been moved to plugins that need to be *pip installed* separately.
See [this documentation page](https://crivella.github.io/ocr_translate/user/index.html) for a list of validated plugins.

Run the server using for example one of the following options:

- Django development server. This is more oriented for developing than deploying, but is fine for a self-hosted single-user server accepting connections only on *localhost*
  - From inside the project directory:

        python manage.py runserver PORT

  - The suggested PORT would be 4000 as it is the one set by default in the extension
- [Nginx](https://www.nginx.com/) + [Gunicorn](https://gunicorn.org/):
  - Check the [Dockerfile](Dockerfile), as this is what the provided image makes use of.

At least for the first time, it is suggested to run the server with the [Environment variables](#environment-variables) `AUTOCREATE_LANGUAGES` and `AUTOCREATE_VALIDATED_MODELS` set to `"true"` to automatically load the validated languages and models provided by the project.

Notes:

- Gunicorn workers will each spawn a separate instance of the loaded models, each taking its own space in the memory. This can quickly fill up the memory especially if running on GPU. Ideally set this to 1.
- Django development server will spawn new threads for handling incoming requests (if no currently existing thread is free), which share the same memory. Running more than one worker per loaded model concurrently might slow down the actual computation and in some case also block the execution.

**SuperUser**: You can create a superuser for managing the database via the django-admin interface by running

    python manage.py createsuperuser

### From PyPI installation

Run the command

    pip install django-ocr_translate

By default torch 2.x will come in its CUDA enabled version. While this works also for CPU, it will also install ~1 GB of cuda dependencies.
If you wish to run on CPU only, download the file [requirements-torch-cpu.txt](requirements-torch-cpu.txt) first and run

    pip install -r requirements-torch-cpu.txt

before installing the python package.

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

CPU and CUDA specific images are available on [DockerHUB](https://hub.docker.com/r/crivella1/ocr_translate):

Download the image from DockerHUB:

- CPU: `docker pull crivella1/ocr_translate:latest-cpu`
- GPU: `docker pull crivella1/ocr_translate:latest-gpu`

or create it manually create your image:

- Create a .pip-cache-[cpu/gpu] directory inside your project.
- Optional: re-install the project dependencies pointing this as the cache folder for pip (will make the build process much faster, by reusing the cached dependencies)
- Run `docker build -t IMAGE_TAG -f Dockerfile-[cpu/gpu] .`

Run the command:

    docker run --name CONTAINER_NAME -v PATH_TO_YOUR_MODEL_DIRECTORY:/models -v PATH_TO_DIR_WITH_SQLITE_FILE:/data --env-file=PATH_TO_AND_ENV_VARIABLE_FILE -p SERVER_PORT:4000 -d ocr_translate

See the [Environment variables](#environment-variables) section for configuring your environment variable file. Additionally the docker image defines several other variables to automatically create an admin user for managing the database via the django-admin interface:

- `UID`: UID of the user owning the files in /models and /data
- `GID`: GID of the user owning the files in /models and /data
- `NUM_WEB_WORKERS`: Number of gunicorn workers for the server
- `DJANGO_SUPERUSER_USERNAME`: The username of the admin user to be created.
- `DJANGO_SUPERUSER_PASSWORD`: The password of the admin user to be created.
