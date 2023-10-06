
User's guide
============

.. toctree::
   :maxdepth: 2

   envs

Known validated plugins
-----------------------

- `ocr_translate-hugging_face <https://github.com/Crivella/ocr_translate-hugging_face>`_: Enables usage of HuggingFace VED models for OCR and seq2seq models for translations.
- `ocr_translate-easyocr <https://github.com/Crivella/ocr_translate-easyocr>`_: Enables usage of easyocr for Box detection.
- `ocr_translate-tesseract <https://github.com/Crivella/ocr_translate-google>`_: Enables usage of tesseract for OCR (tesseract need to be installed on the pc).
- `ocr_translate-google <https://github.com/Crivella/ocr_translate-google>`_: Enables usage of GoogleTranslate for translations.

Supported/tested databases
--------------------------

- `SQLite <https://www.sqlite.org/>`_: This is mostly fine for a self-hosted server accessed by a single  or few users (and it's probably gonna be faster than any other database not running on the same network as the server because of latency).
- `MySQL <https://www.mysql.com/>`_
- `MariaDB <https://mariadb.org/>`_
- `PostgreSQL <https://www.postgresql.org/>`_
