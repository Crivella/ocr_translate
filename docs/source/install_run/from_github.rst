From Github
-----------

This assumes you have access to a terminal and have `python` and `git` installed on your system.

- Clone or download the repository

  - :code:`git clone https://github.com/Crivella/ocr_translate.git`
  - :code:`cd ocr_translate`

- (Optional) create and use a `virtual environment <https://docs.python.org/3/library/venv.html>`_

  - :code:`python -m venv venv`
  - :code:`venv\Scripts\activate`

- Install the project and its dependencies
  - :code:`pip install .`

The Github repo provides not only the Django app files, but also the already configured project files used to start the server.

.. _github_run_server:

Run the server
______________

You can either use the :code:`run_server.py` script that will bootstrap the server for you,

- :code:`python run_server.py`

or manually run the Django server.

- Create/Initialize your database by running

  - :code:`python manage.py migrate`

  inside your project folder.

- Run the server:

  - With the Django development server. This is more oriented for developing than deploying, but is fine for a self-hosted single-user server accepting connections only on *localhost*

    - :code:`python manage.py runserver PORT`
    - The suggested PORT would be 4000 as it is the one set by default in the extension

  - `Nginx <https://www.nginx.com/>`_ + `Gunicorn <https://gunicorn.org/>`_ (Linux only):

    - Check :code:`Dockerfile` and :code:`run_server.py` files, as this is what the provided docker image makes use of.

At least for the first time, it is suggested to run the server with the :doc:`Environment variable <../user/envs>` `AUTOCREATE_LANGUAGES` set to `"true"` to automatically load the validated languages and models provided by the project.

Notes
-----

- Gunicorn workers will each spawn a separate instance of the loaded models, each taking its own space in the memory. This can quickly fill up the memory especially if running on GPU. Ideally set this to 1.
- Django development server will spawn new threads for handling incoming requests (if no currently existing thread is free), which share the same memory. Running more than one worker per loaded model concurrently might slow down the actual computation and in some case also block the execution.
