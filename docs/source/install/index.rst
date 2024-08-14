
Installation
====================

NOTE!!: Since version `v0.6`, `python` (or at least) `pip` needs to be installed on the system. (See https://www.python.org/downloads/)

.. toctree::
   :maxdepth: 3

From Release file (Windows only)
--------------------------------


- Make sure to have `python ,https://www.python.org/downloads/windows/`_ (3.11 suggested) installed on your system and available in the PATH (There is a checkbox that you need to tick as soon as you run the installer to automatically do this).
- From :github:`github <releases/>` download the :github:`release file <releases/latest/download/run_server.zip>`
- Extract the content of the zip file in a folder of your choice
- Run the :code:`run_server.exe` file

The server will run with sensible defaults. Most notably the models files, plugin files (needed python packages) and database will be downloaded/created under :code:`%userprofile%/.ocr_translate`.

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

From Docker
-----------

Images are available on :dockerhub:`Dockerhub <>`:

- :code:`docker pull crivella1/ocr_translate:latest`

Manually create your image:

- :code:`git clone https://github.com/Crivella/ocr_translate.git`
- :code:`cd ocr_translate`
- :code:`docker build -t IMAGE_TAG -f Dockerfile .`

From PyPI
---------

Run the command

- (Optional) create and use a `virtual environment <https://docs.python.org/3/library/venv.html>`_

  - :code:`python -m venv venv`
  - :code:`venv\Scripts\activate`

- :code:`pip install django-ocr_translate`
