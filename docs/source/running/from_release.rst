From Release (Windows)
----------------------

Tested for Windows11

- Unzip the release file downloaded in the previous step.
- From inside the folder, run the :code:`run_server-XXX.exe` file (XXX=cpu/gpu)

The server will run with sensible defaults. Most notably the models files and database will be downloaded/created under `%userprofile%/.ocr_translate`.
Also the gpu version will attempt to run on GPU by default, and fall-back to CPU if the former is not available.

For customization, you can set the :doc:`Environment variables <../user/envs>` yourself:

- Powershell:

.. code-block:: powershell

    $env:ENV_VAR_NAME="XXX"

- by searching for :code:`environment variable` in the settings menu.
