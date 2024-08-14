Install and Run
===============


.. toctree::
    :maxdepth: 2

    from_release
    from_github
    from_pypi
    from_docker

General info
------------

NOTE!!: Since version `v0.6`, `python` (or at least) `pip` needs to be installed on the system. (See https://www.python.org/downloads/)

Most of the server behavior the behavior of the server (eg: model/plugin/db install locations and allowed hosts) can be customized using :doc:`Environment variables <../user/envs>`

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
