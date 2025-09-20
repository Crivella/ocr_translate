Environment Variables
=====================

The server will check a number of environment variables to configure itself.

Setting Environment variables
-----------------------------

Environment variables can be set in many ways depending on the the OS and/or the tool used to launch the server.
This is a list of common possible ways:

- Windows Powershell: :code:`$env:VARIABLE_NAME = "value"` (code must be run in the same shell)
- Windows Command Prompt: :code:`set VARIABLE_NAME=value` (code must be run in the same shell)
  !! Do not use quotes as they will be included in the value
- Windows Settings: :code:`Control Panel > System > Advanced System Settings > Environment Variables`
- Linux BASH: :code:`export VARIABLE_NAME=value` (code must be run in the same shell)
- VSCode: :code:`launch.json > env > VARIABLE_NAME`

.. code-block::

    {
        "version": "0.2.0",
        "configurations": [
            {
                ...
                "env": {
                    "VARIABLE_NAME_1": "VALUE_1",
                    ...
                },
                ...
            }
        ]
    }

- Docker: :code:`docker run -e VARIABLE_NAME=value ...`
- Docker: :code:`docker run --env-file .env ...` where `.env` is a file with the format

.. code-block::

    VARIABLE_NAME_1=VALUE_1
    ...
    VARIABLE_NAME_N=VALUE_N

.. Include:: ./_env_vars.rst

Docker exceptions
-------------------------

In Docker environments, the values of :code:`OCT_DJANGO_PORT` and :code:`OCT_BASE_DIR` are overridden and cannot be customized.

To persist data, bind mount the container path :code:`/plugin_data`. The server listens on port :code:`4000`, which should be mapped to the desired host port.
