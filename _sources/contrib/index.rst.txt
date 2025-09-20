Contributor's guide
===================

.. toctree::
   :maxdepth: 2

   plugins
   api

This is the guide for contributing to the main codebase of the project.

Development dependencies
------------------------

When installing the python package with pip you can install various sets of optional dependencies.
For development you should install django-ocr_translate (from inside a clone of your fork) with the following:

.. code-block:: shell

   pip install .[tests,pre-commit]

If you also plan to add to the documentation than you should install the `docs` dependencies:

.. code-block:: shell

   pip install .[docs]

pre-commit hooks
----------------

Once the python extra dependencies are installed, install the `pre-commit <https://pre-commit.com/>`_ hooks into your repo. These are used to enforce code style and run tests before commits. (This will be enforced on pull requests by the CI workflow, so you might as well do it from the beginning)

.. code-block:: shell

   pre-commit install

You can also manually run the pre-commit command on all files:

.. code-block:: shell

   pre-commit run --all-files

Note that some of the hooks will modify the files in place, so you might need to re-add them to the staging area.

Testing
-------

If you are adding new code to the codebase, make sure to add tests for it.
You can check if your code is covered by tests by running:

.. code-block:: shell

   pytest --cov=ocr_translate --cov-report=html tests

And opening the `htmlcov/index.html` file generated in your working directory.

If you are running tests with and IDE like VSCode, make sure that the following is set in your environment.

.. code-block::

   `DJANGO_SETTINGS_MODULE = "ocr_translate.app.settings"`
