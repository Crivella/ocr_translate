
Running
====================

This is a guide on running the ocr_translate server using different methods.

.. toctree::
    :maxdepth: 2

    from_release
    from_github
    from_pypi
    from_docker

General info
------------

If you plan to use a different settings (eg. database, or model location), you can either:

- Manually edit the :code:`settings.py` file
- Use the provided :doc:`Environment variables <../user/envs>`

See below for a :doc:`list of supported databases <../user/index>`

You will also have to modify the :code:`ALLOWED_HOSTS` in case you plan to access the server from somewhere other than `localhost`.

All the different way to run the server may provide different set of default values (each of them is targeted for a different level of usage).

.. _settings.py: mysite/settings.py
