Plugins
=======

Plugins are the bread and butter of `ocr_translate`.

The base project implements functionalities to handle the web server, database, translation pipelines and queues.

How and which models are used is implemented entirely in plugins.

Plugins can be installed by using the plugin collapsable menu on the extension, by directly using the `manage_plugins/` endpoint (:doc:`see here <../contrib/api>`) or by manually installing them in the server environment.

ocr_translate-hugging_face
--------------------------

`HOMEPAGE <https://github.com/Crivella/ocr_translate-hugging_face>`__

Plugin for using Hugging Face models for OCR and translation.

Implements `VED models <https://huggingface.co/docs/transformers/en/model_doc/vision-encoder-decoder>`_ for OCR and `Seq2Seq <https://huggingface.co/learn/nlp-course/en/chapter1/7>`_ models for translation.

Plugin or associated packages environment variables

.. list-table:: Title
    :widths: 16 16 68
    :header-rows: 1

    * - Variable
      - Default
      - Usage
    * - :code:`TRANSFORMERS_CACHE`
      - :code:`$OCT_BASE_DIR/models/huggingface`
      - Directory where `Hugging Face <https://huggingface.co/>`_ models are being

        stored (either downloaded manually or downloaded

        by `transformers`)
    * - :code:`TRANSFORMERS_OFFLINE`
      - 0
      - By default `transformers` will try to download

        missing models. Set this to 1 to only work in

        offline mode

ocr_translate-easyocr
---------------------

`HOMEPAGE <https://github.com/Crivella/ocr_translate-easyocr>`__

Plugin for using EasyOCR models for BBox detection.

Plugin or associated packages environment variables

.. list-table:: Title
    :widths: 16 16 68
    :header-rows: 1

    * - Variable
      - Default
      - Usage
    * - :code:`EASYOCR_PREFIX`
      - :code:`$OCT_BASE_DIR/models/easyocr`
      - Directory where EasyOCR downloads its models

ocr_translate-tesseract
-----------------------

`HOMEPAGE <https://github.com/Crivella/ocr_translate-tesseract>`__

Plugin for using Tesseract models for OCR.
This requires tesseract to be installed on your machine.

Plugin or associated packages environment variables

.. list-table:: Title
    :widths: 16 16 68
    :header-rows: 1

    * - Variable
      - Default
      - Usage
    * - :code:`TESSERACT_PREFIX`
      - :code:`$OCT_BASE_DIR/models/tesseract`
      - Directory where tesseract downloads its models

    * - :code:`TESSERACT_ALLOW_DOWNLOAD`
      - true
      - Control whether the app should download missing

        models (true) or work in offline mode only (false)

ocr_translate-paddle
--------------------

`HOMEPAGE <https://github.com/Crivella/ocr_translate-paddle>`__

Plugin for using PaddleOCR models for BBox detection and OCR.

.. list-table:: Title
    :widths: 16 16 68
    :header-rows: 1

    * - Variable
      - Default
      - Usage
    * - :code:`PADDLEOCR_PREFIX`
      - :code:`$OCT_BASE_DIR/models/paddleocr`
      - Directory where PaddleOCR downloads its models

ocr_translate-ollama
--------------------

`HOMEPAGE <https://github.com/Crivella/ocr_translate-ollama>`__

Plugin for using LLMs through ollama for translation.

The `Ollama <https://ollama.com/>`_ server needs to be setup independently.

.. list-table:: Title
    :widths: 16 16 68
    :header-rows: 1

    * - Variable
      - Default
      - Usage
    * - :code:`OCT_OLLAMA_ENDPOINT`
      - :code:`http://127.0.0.1:11434/api`
      - Endpoint where the ollama server is running


ocr_translate-google
--------------------

`HOMEPAGE <https://github.com/Crivella/ocr_translate-google>`__

Plugin for using Google Translate for translation.

This plugins requires an internet connection and will send the text to be translated to google.

.. list-table:: Title
    :widths: 16 16 68
    :header-rows: 1

    * - Variable
      - Default
      - Usage
    * - EMPTY
      - EMPTY
      - EMPTY
