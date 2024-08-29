From Docker image
-----------------

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


Compose example
_______________

This is an example of using :code:`docker compose` to run the server with a postgres database and bind mounts:

- Create a :code:`docker-compose.yml` file with the following content:

.. code-block:: yaml

    name: ocr_translate

    services:
      server:
        container_name: oct_server
        image: crivella1/ocr_translate:0.6.0
        volumes:
          - ${PLUGINS_LOCATION}:/plugin_data
          - ${MODELS_LOCATION}:/models
        env_file:
          - .env
        environment:
          - DATABASE_NAME=${DB_DATABASE_NAME}
          - DATABASE_ENGINE=django.db.backends.postgresql
          - DATABASE_USER=${DB_USERNAME}
          - DATABASE_PASSWORD=${DB_PASSWORD}
          - DATABASE_HOST=database
          - DATABASE_PORT=5432
        ports:
          - 4000:4000
        depends_on:
          - database
        restart: unless-stopped

      database:
        container_name: oct_postgres
        image: postgres:16.4
        environment:
          POSTGRES_PASSWORD: ${DB_PASSWORD}
          POSTGRES_USER: ${DB_USERNAME}
          POSTGRES_DB: ${DB_DATABASE_NAME}
          POSTGRES_INITDB_ARGS: '--data-checksums'
        volumes:
          - ${DB_DATA_LOCATION}:/var/lib/postgresql/data
        healthcheck:
          test: pg_isready --dbname='${DB_DATABASE_NAME}' --username='${DB_USERNAME}' || exit 1; Chksum="$$(psql --dbname='${DB_DATABASE_NAME}' --username='${DB_USERNAME}' --tuples-only --no-align --command='SELECT COALESCE(SUM(checksum_failures), 0) FROM pg_stat_database')"; echo "checksum failure count is $$Chksum"; [ "$$Chksum" = '0' ] || exit 1
          interval: 5m
          start_interval: 30s
          start_period: 5m
        restart: unless-stopped

- Create a :code:`.env` file with the following content (replace the values with your own):

.. code-block:: sh

    PLUGINS_LOCATION=./plugins
    MODELS_LOCATION=./models
    DB_DATA_LOCATION=./data

    DB_USERNAME=postgres
    DB_DATABASE_NAME=ocr_translate

    # Connection password for postgres. You should change it to a random password
    DB_PASSWORD=YOUR_DATABASE_PASSWORD

- Run the command:

.. code-block:: bash

    docker-compose up -d
