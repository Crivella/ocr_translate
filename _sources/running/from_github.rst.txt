From Github installation
------------------------

See the section on how to :doc:`install from Github </install/index>` first.

The Github repo provides not only the Django app files, but also the already configured project files used to start the server.

Create/Initialize your database by running

- :code:`python manage.py migrate`

inside your project folder.

Run the server using for example one of the following options:

- Django development server. This is more oriented for developing than deploying, but is fine for a self-hosted single-user server accepting connections only on *localhost*
  - From inside the project directory: :code:`python manage.py runserver PORT`
  - The suggested PORT would be 4000 as it is the one set by default in the extension
- `Nginx <https://www.nginx.com/>`_ + `Gunicorn <https://gunicorn.org/>`_:
  - Check the :code:`Dockerfile`, as this is what the provided image makes use of.

At least for the first time, it is suggested to run the server with the :doc:`Environment variables <../user/envs>` `AUTOCREATE_LANGUAGES` and `AUTOCREATE_VALIDATED_MODELS` set to `"true"` to automatically load the validated languages and models provided by the project.

Notes:

- Gunicorn workers will each spawn a separate instance of the loaded models, each taking its own space in the memory. This can quickly fill up the memory especially if running on GPU. Ideally set this to 1.
- Django development server will spawn new threads for handling incoming requests (if no currently existing thread is free), which share the same memory. Running more than one worker per loaded model concurrently might slow down the actual computation and in some case also block the execution.
