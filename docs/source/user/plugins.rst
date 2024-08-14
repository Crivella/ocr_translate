Kwnown plugins
==============

This is a list of known and approved plugins available for install in the server.

ocr_translate-hugging_face
--------------------------

`HOMEPAGE <https://github.com/Crivella/ocr_translate-hugging_face>`_

Plugin for using Hugging Face models for OCR and translation.

Plugin or associated packages environment variables

.. list-table:: Title
    :widths: 16 16 68
    :header-rows: 1

    * - Variable
      - Values
      - Usage
    * - :code:`TRANSFORMERS_CACHE`
      - :code:`$OCT_BASE_DIR`
      - Directory where `Hugging Face <https://huggingface.co/>`_ models are being

        stored (either downloaded manually or downloaded

        by `transformers`)
    * - :code:`TRANSFORMERS_OFFLINE`
      - 1[/0]
      - By default `transformers` will try to download

        missing models. Set this to 0 to only work in

        offline mode

ocr_translate-easyocr
---------------------

`HOMEPAGE <https://github.com/Crivella/ocr_translate-easyocr>`_

Plugin for using EasyOCR models for BBox detection.

Plugin or associated packages environment variables

.. list-table:: Title
    :widths: 16 16 68
    :header-rows: 1

    * - Variable
      - Values
      - Usage
    * - :code:`EASYOCR_MODULE_PATH`
      - :code:`$HOME/.EasyOCR`
      - Directory where EasyOCR store its downloaded

        models

ocr_translate-tesseract
-----------------------

`HOMEPAGE <https://github.com/Crivella/ocr_translate-tesseract>`_

Plugin for using Tesseract models for OCR.
This requires tesseract to be installed on your machine.

Plugin or associated packages environment variables

.. list-table:: Title
    :widths: 16 16 68
    :header-rows: 1

    * - Variable
      - Values
      - Usage
    * - :code:`TESSERACT_PREFIX`
      - :code:`$TRANSFORMERS_CACHE/tesseract`
      - Directory where tesseract will store and look

        for models
    * - :code:`TESSERACT_ALLOW_DOWNLOAD`
      - true
      - Control whether the app should download missing

        models (true) or work in offline mode only (false)

ocr_translate-paddle
--------------------

`HOMEPAGE <https://github.com/Crivella/ocr_translate-paddle>`_

Plugin for using PaddleOCR models for BBox detection and OCR.

.. list-table:: Title
    :widths: 16 16 68
    :header-rows: 1

    * - Variable
      - Values
      - Usage
    * - :code:`PADDLEOCR_PREFIX`
      - :code:`$TRANSFORMERS_CACHE/tesseract`
      - Directory where PaddleOCR will store and look

        for models

ocr_translate-ollama
--------------------

`HOMEPAGE <https://github.com/Crivella/ocr_translate-paddle>`_

Plugin for using LLMs through ollama for translation.

.. list-table:: Title
    :widths: 16 16 68
    :header-rows: 1

    * - Variable
      - Values
      - Usage
    * - :code:`PADDLEOCR_PREFIX`
      - :code:`$TRANSFORMERS_CACHE/tesseract`
      - Directory where PaddleOCR will store and look

        for models


.. - [e]():
.. - [ocr_translate-ollama](https://github.com/Crivella/ocr_translate-ollama):
.. - [ocr_translate-google](https://github.com/Crivella/ocr_translate-google): Plugin for using Google Translate for translation. -->
