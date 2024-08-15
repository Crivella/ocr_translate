From Release File (Windows)
---------------------------

Tested for Windows11

- Make sure to have `python <https://www.python.org/downloads/windows/>`_ (3.11 suggested) installed on your system and available in the PATH (There is a checkbox that you need to tick as soon as you run the installer to automatically do this).

.. image:: windows_python_install.png
    :alt: Python installer
    :align: center

- From :github:`github <releases/>` download the :github:`release file <releases/latest/download/run_server.zip>`
- Extract the content of the zip file in a folder of your choice
- Run the :code:`run_server.exe` file
- Unzip the release file downloaded in the previous step.
- From inside the folder, run the :code:`run_server.exe`

The server will run with sensible defaults.
Most notably the models files, plugin files (needed python packages) and database will be downloaded/created under :code:`%userprofile%/.ocr_translate`.
If not DEVICE is specified, the server will attempt to find the :code:`nvidia-smi` executable and if available, will run on GPU.

For customization, you can set the :doc:`Environment variables <../user/envs>` yourself:

- Powershell:

.. code-block:: powershell

    $env:ENV_VAR_NAME="XXX"

- by searching for :code:`environment variable` in the settings menu.
