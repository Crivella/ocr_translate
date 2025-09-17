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

Most of the server behavior (eg: model/plugin/db install locations and allowed hosts) can be customized using :doc:`Environment variables <../user/envs>`

SuperUser
---------

Following the described procedures, the server will be created with a admin user *admin*:*password*.

The username and password can be changed by setting the environment variables `DJANGO_SUPERUSER_USERNAME` and `DJANGO_SUPERUSER_PASSWORD` respectively. (See :doc:`Environment variables <../user/envs>`)

You can login to the admin interface at `http://SERVER_ADDRESS:SERVER_PORT/admin/` (eg: `http://127.0.0.1:4000/admin/`) in order to manage the database.
The main idea is to use this to manually add new models (with the appropriate entrypoint) if you want to test out,
model that are not yet available. (If you find good models, please do share).

GPU
---

By default the `run_server.py` will attempt to use a specific device following:

- If the environment variable `DEVICE` is set, it will use the device specified by the value.
- If `nvidia-smi` is available the server will try running in GPU mode.
- If none of the above is available, the server will run in CPU mode.

Independent of the configured specified/found `DEVICE`, if `torch` is already installed it will be used to determine if it can run with CUDA.

As of `v0.6` no device specific dependencies are included by default, but some plugins will install/use different dependencies based on the device used.
