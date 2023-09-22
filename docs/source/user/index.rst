
User's guide
============

.. toctree::
   :maxdepth: 2

   envs

Known validated plugins
-----------------------

- `ocr_translate-google <https://github.com/Crivella/ocr_translate-google>`_: Enables usage of GoogleTranslate for translations.

Supported/tested databases
--------------------------

- `SQLite <https://www.sqlite.org/>`_: This is mostly fine for a self-hosted server accessed by a single  or few users (and it's probably gonna be faster than any other database not running on the same network as the server because of latency).
- `MySQL <https://www.mysql.com/>`_
- `MariaDB <https://mariadb.org/>`_
- `PostgreSQL <https://www.postgresql.org/>`_