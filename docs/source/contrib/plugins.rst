Writing plugins
===============

New models and proxy model classes can be added without modifying the core codebase by creating a python package and using the following entrypoints.

IMPORTANT: The model class are supposed to be proxy classes  and should ence contain

.. code-block:: python

    class Meta:
        proxy = True

- :code:`ocr_translate.box_data`: Point this entrypoint to a dictionary with the info required to create a new :code:`OCRBoxModel`

.. code-block:: python

    easyocr_box_model_data = {
        # Name of the model
        'name': 'easyocr',
        # List of ISO-639-1 codes supported by the model
        'lang': ['en', 'ja', 'zh', 'ko'],
        # How the model requires the codes to be passed (one of 'iso1', 'iso2b', 'iso2t', 'iso3')
        # If the models codes only partially match or are totally different from one of the ISO standards, see iso1_map
        'lang_code': 'iso1',
        # Name of the entrypoint for the model (should match what is used in pyproject.toml)
        'entrypoint': 'easyocr.box',
        # Maps ISO-639-1 codes to the codes used by the model. Does not need to map every language, only those that are
        # different from getattr(lang: m.Language, lang_code)
        'iso1_map': {
            'ce': 'che',
            'zh': 'ch_sim',
            'zht': 'ch_tra',
            'tg': 'tjk',
        }
    }

- :code:`ocr_translate.ocr_data`: Point this entrypoint to a dictionary with the info required to create a new :code:`OCRModel`

.. code-block:: python

    khawhite_ocr_model_data = {
        'name': 'kha-white/manga-ocr-base',
        'lang': ['ja'],
        'lang_code': 'iso1',
        'entrypoint': 'hugginface.ved'
    }

- :code:`ocr_translate.tsl_data`: Point this entrypoint to a dictionary with the info required to create a new :code:`TSLModel`

.. code-block:: python

    staka_fugumt_ja_en_tsl_model_data = {
        'name': 'staka/fugumt-ja-en',
        'lang_src': ['ja'],
        'lang_dst': ['en'],
        'lang_code': 'iso1',
        'default_options': {
            'break_newlines': True
        },
        'entrypoint': 'hugginface.seq2seq'
    }

- :code:`ocr_translate.box_models`: Point this entrypoint to a class that subclasses :code:`OCRBoxModel`. Should redefine atleast the following methods

.. code-block:: python

    class NewProxyOCRBoxModel(m.OCRBoxModel):
        """OCRBoxtranslate plugin to allow usage of ... for box detection."""
        class Meta:
            proxy = True

        def load(self):
            """Load the model into memory."""
            # DO something here to load the model or nothing if not needed (should still be defined)

        def unload(self) -> None:
            """Unload the model from memory."""
            # DO something here to unload the model or nothing if not needed (should still be defined)


        def _box_detection(
                self,
                image: PILImage, options: dict = None
                ) -> list[tuple[int, int, int, int]]:
            """Perform box OCR on an image.

            Args:
                image (Image.Image): A Pillow image on which to perform OCR.
                options (dict, optional): A dictionary of options.

            Raises:
                NotImplementedError: The type of model specified is not implemented.

            Returns:
                list[tuple[int, int, int, int]]: A list of bounding boxes in lrbt format.
            """
            # Redefine this method with the same signature as above
            # Should return a list of `lrbt` boxes after processing the input PILImage
