
Installation
====================

For both the Githyb and PyPI installation it is strongly suggested to install this project using a `virtual environment <https://docs.python.org/3/library/venv.html>`_.

.. toctree::
   :maxdepth: 3

From Release file (Windows only)
--------------------------------

From the :github:`github releases page <releases/>` you can download either:

- The :github:`CPU only version <releases/latest/download/run_server-cpu.zip>`
- The GPU version split in :github:`file1 <releases/latest/download/run_server-gpu.zip.001>` and :github:`file2 <releases/latest/download/run_server-gpu.zip.002>` (The CUDA dependencies makes it take much more space), wich can be restored using tools like `7zip <https://www.7-zip.org/https://www.7-zip.org/>`_ and `NanaZip <https://github.com/M2Team/NanaZip>`_.

From Github
-----------

- Clone or download the repository
  - :code:`git clone https://github.com/Crivella/ocr_translate.git`
- Install the project dependencies (choose the appropriate files depending if you wanna run on GPU or CPU only):
  - :code:`pip install -r requirements-torch-[cpu/cuda].txt`
  - :code:`pip install -r requirementscs.txt`

From Docker
-----------

CPU and CUDA specific images are available on :dockerhub:`Dockerhub <>`:

- CPU: :code:`docker pull crivella1/ocr_translate:latest-cpu`
- GPU: :code:`docker pull crivella1/ocr_translate:latest-gpu`

Manually create your image:

- Create a .pip-cache-[cpu/gpu] directory inside your project.
- Optional: re-install the project dependencies pointing this as the cache folder for pip (will make the build process much faster, by reusing the cached dependencies)
- Run :code:`docker build -t IMAGE_TAG -f Dockerfile-[cpu/gpu] .`

From PyPI
---------

Run the command

- :code:`pip install django-ocr_translate`

By default torch 2.x will come in its CUDA enabled version. While this works also for CPU, it will also install ~1 GB of cuda dependencies.
If you wish to run on CPU only, download the file [requirements-torch-cpu.txt](requirements-torch-cpu.txt) first and run

- :code:`pip install -r requirements-torch-cpu.txt`

before installing the python package.
