From Docker image
-----------------

See the section on how to :doc:`install from DockerHUB </install/index>` first.

This section assumes you have docker installed and the image of the project.

Run the command:

- :code:`docker run --name CONTAINER_NAME -v PATH_TO_YOUR_MODEL_DIRECTORY:/models -v PATH_TO_DIR_WITH_SQLITE_FILE:/data --env-file=PATH_TO_AND_ENV_VARIABLE_FILE -p SERVER_PORT:4000 -d ocr_translate`

See the [Environment variables](#environment-variables) section for configuring your environment variable file. Additionaly the docker image defines several other variables to automatically create an admin user for managing the database via the django-admin interface:

- :code:`UID`: UID of the user owning the files in /models and /data
- :code:`GID`: GID of the user owning the files in /models and /data
- :code:`NUM_WEB_WORKERS`: Number of gunicorn workers for the server
- :code:`DJANGO_SUPERUSER_USERNAME`: The username of the admin user to be created.
- :code:`DJANGO_SUPERUSER_PASSWORD`: The password of the admin user to be created.
