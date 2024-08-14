From Docker image
-----------------

See the section on how to :doc:`install from DockerHUB </install/index>` first if you don't have it already.

Images can be downloaded from :dockerhub:`Dockerhub <>`:

- :code:`docker pull crivella1/ocr_translate:latest`

Or manually created:

- :code:`git clone https://github.com/Crivella/ocr_translate.git`
- :code:`cd ocr_translate`
- :code:`docker build -t IMAGE_TAG -f Dockerfile .`

Run the command:

- :code:`docker run --name CONTAINER_NAME -v OCT_MODELS:/models -v OCT_DB_DATA:/db_data -v OCT_PLUGINS_DATA:/plugins_data -p SERVER_PORT:4000 -d IMAGE_NAME`

Replace the all caps parts with the appropriate values.
For the volumes you can either specify a native docker volume using a name or a bind mount using a path (see `docker documentation <https://docs.docker.com/storage/volumes/>``).
While it is possible to omit the `-v` this will result in a new volume with random name being created each time the container is run, making it hard to reuse previous data.

See the :doc:`Environment variables <../user/envs>` section for configuring your environment variables via CLI or a file.

Additionally the docker image defines several other variables to automatically create an admin user for managing the database via the django-admin interface:

- :code:`UID`: UID of the user owning the files in /models and /data
- :code:`GID`: GID of the user owning the files in /models and /data
- :code:`NUM_WEB_WORKERS`: Number of gunicorn workers for the server
- :code:`DJANGO_SUPERUSER_USERNAME`: The username of the admin user to be created.
- :code:`DJANGO_SUPERUSER_PASSWORD`: The password of the admin user to be created.
