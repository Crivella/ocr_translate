Writing plugins
===============

New models and proxy model classes can be added without modifying the core codebase by creating a python package and using the following entrypoints.

When Creating a plugin, the following example show the minimal methods that need to be redefined.
Beside this, the plugin can also redefine any of the methods to change eg how inputs are preprocessed, but be careful with this as it might break provenance (eg. `options` are used differently).

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

    class SomeNewClassName(m.OCRBoxModel):
        """OCRBoxtranslate plugin to allow usage of ... for box detection."""
        class Meta:
            proxy = True

        def load(self):
            """Load the model into memory."""
            # Do something here to load the model or nothing if not needed (should still be defined)

        def unload(self) -> None:
            """Unload the model from memory."""
            # Do something here to unload the model or nothing if not needed (should still be defined)


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

- :code:`ocr_translate.ocr_models`: Point this entrypoint to a class that subclasses :code:`OCRModel`. Should redefine atleast the following methods

.. code-block:: python

    class SomeNewClassName(m.OCRModel):
        """OCRBoxtranslate plugin to allow usage of ... for box detection."""
        class Meta:
            proxy = True

        def load(self):
            """Load the model into memory."""
            # Do something here to load the model or nothing if not needed (should still be defined)

        def unload(self) -> None:
            """Unload the model from memory."""
            # Do something here to unload the model or nothing if not needed (should still be defined)


        def _ocr(
                self,
                img: Image.Image, lang: str = None, options: dict = None
                ) -> str:
            """Perform OCR on an image.

            Args:
                img (Image.Image):  A Pillow image on which to perform OCR.
                lang (str, optional): The language to use for OCR. (Not every model will use this)
                bbox (tuple[int, int, int, int], optional): The bounding box of the text on the image in lbrt format.
                options (dict, optional): A dictionary of options to pass to the OCR model.

            Raises:
                TypeError: If img is not a Pillow image.

            Returns:
                str: The text extracted from the image.
            """
            # Redefine this method with the same signature as above
            # Should return a sring with the result of the OCR performed on the input PILImage.
            # Unless the methods `prepare_image` or `ocr` are also being overwritten, the input image will be the result of the CROP on the original image using the bounding boxes given by the box detection model.

- :code:`ocr_translate.tsl_models`: Point this entrypoint to a class that subclasses :code:`TSLModel`. Should redefine atleast the following methods

.. code-block:: python

    class SomeNewClassName(m.TSLModel):
        """OCRBoxtranslate plugin to allow usage of ... for box detection."""
        class Meta:
            proxy = True

        def load(self):
            """Load the model into memory."""
            # Do something here to load the model or nothing if not needed (should still be defined)

        def unload(self) -> None:
            """Unload the model from memory."""
            # Do something here to unload the model or nothing if not needed (should still be defined)


        def _translate(
                self,
                tokens: list, src_lang: str, dst_lang: str, options: dict = None) -> str | list[str]:
            """Translate a text using a the loaded model.

            Args:
                tokens (list): list or list[list] of string tokens to be translated.
                lang_src (str): Source language.
                lang_dst (str): Destination language.
                options (dict, optional): Options for the translation. Defaults to {}.

            Raises:
                TypeError: If text is not a string or a list of strings.

            Returns:
                Union[str,list[str]]: Translated text. If text is a list, returns a list of translated strings.
            """
            # Redefine this method with the same signature as above
            # Should return a sring with the translated text.
            # IMPORTANT: the main codebase treats this function as batchable:
            # The input `tokens` can be a list of strings or a list of list of strings. The output should match the input being a string or list of strings.
            # (This is used to leverage the capability of pytorch to batch inputs and outputs for faster performances, or it can also used to write a plugin for an online service by using a single request for multiple inputs using some separator that the service will leave unaltered.)
