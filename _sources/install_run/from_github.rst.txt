From Github
-----------

This assumes you have access to a terminal and have `python` and `git` installed on your system.

- Clone or download the repository

  - :code:`git clone https://github.com/Crivella/ocr_translate.git`
  - :code:`cd ocr_translate`

- (Optional) create and use a `virtual environment <https://docs.python.org/3/library/venv.html>`_

  - :code:`python -m venv venv`
  - :code:`venv\\Scripts\\activate` (or the equivalent for your OS)

- Install the project and its dependencies
  - :code:`pip install .`

The Github repo provides not only the Django app files, but also the already configured project files used to start the server.

.. _github_run_server:

Run the server
______________

You can either use the :code:`run_server.py` script that will bootstrap the server for you,

- OPTIONAL: Install ``gunicorn`` in your environment to use it instead of the django development server.
- :code:`python release_files/run_server.py`


Notes
_____

- Gunicorn workers will each spawn a separate instance of the loaded models, each taking its own space in the memory. This can quickly fill up the memory especially if running on GPU. Ideally set this to 1.
- Django development server will spawn new threads for handling incoming requests (if no currently existing thread is free), which share the same memory. Running more than one worker per loaded model concurrently might slow down the actual computation and in some case also block the execution.
