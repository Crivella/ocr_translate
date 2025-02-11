###################################################################################
# ocr_translate - a django app to perform OCR and translation of images.          #
# Copyright (C) 2023-present Davide Grassano                                      #
#                                                                                 #
# This program is free software: you can redistribute it and/or modify            #
# it under the terms of the GNU General Public License as published by            #
# the Free Software Foundation, either version 3 of the License.                  #
#                                                                                 #
# This program is distributed in the hope that it will be useful,                 #
# but WITHOUT ANY WARRANTY; without even the implied warranty of                  #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                   #
# GNU General Public License for more details.                                    #
#                                                                                 #
# You should have received a copy of the GNU General Public License               #
# along with this program.  If not, see {http://www.gnu.org/licenses/}.           #
#                                                                                 #
# Home: https://github.com/Crivella/ocr_translate                                 #
###################################################################################
"""Django models for the ocr_translate app."""
import logging
import re
from importlib.metadata import entry_points
from typing import Generator, Type, TypedDict, Union

import numpy as np
from django.db import models
from PIL.Image import Image as PILImage

from . import queues
from .messaging import Message
from .tries import get_trie_src

logger = logging.getLogger('ocr.general')

def get_or_create(model: Type[models.Model], strict: bool = False, **kwargs) -> models.Model:
    """Get or create a model instance in a safe way.

    Args:
        model (Type[models.Model]): The model class to get or create.
        strict (bool, optional): Whether to raise a caught exception if ocurred. Defaults to False.
    """
    try:
        obj, _ = model.objects.get_or_create(**kwargs)
    except model.MultipleObjectsReturned as exc:
        if strict:
            raise exc
        logger.warning(f'Multiple objects returned for {model}: {model.objects.filter(**kwargs).all()}')
        obj = model.objects.filter(**kwargs).first()
    return obj

class OptionDict(models.Model):
    """Dictionary of options for OCR and translation"""
    options = models.JSONField(unique=True)

    def __str__(self):
        return str(self.options)

class Language(models.Model):
    """Language used for translation"""
    name = models.CharField(max_length=64, unique=True)
    iso1 = models.CharField(max_length=8, unique=True)
    iso2b = models.CharField(max_length=8, unique=True)
    iso2t = models.CharField(max_length=8, unique=True)
    iso3 = models.CharField(max_length=32, unique=True)

    default_options = models.ForeignKey(
        OptionDict, on_delete=models.CASCADE, related_name='lang_default_options', null=True
        )

    load_events_src = models.ManyToManyField('LoadEvent', related_name='languages_src')
    load_events_dst = models.ManyToManyField('LoadEvent', related_name='languages_dst')

    def __str__(self):
        return f'{self.name} ({self.iso1})'

    def __eq__(self, other):
        if isinstance(other, Language):
            return self.iso1 == other.iso1
        if isinstance(other, str):
            return self.iso1 == other
        return False

    # https://stackoverflow.com/questions/61212514/django-model-objects-became-not-hashable-after-upgrading-to-django-2-2
    def __hash__(self):
        return hash(self.iso1)

    def load_src(self) -> None:
        """Load the language trie"""
        self.load_events_src.create(description=f'Loading SRC Language {self.name}')

    def load_dst(self) -> None:
        """Load the language trie"""
        self.load_events_dst.create(description=f'Loading DST Language {self.name}')

    @classmethod
    def get_last_loaded_src(cls) -> 'Language':
        """Get the last loaded language"""
        res = cls.objects
        # This is not a problem with SQLite, but with postgres, the order is not guaranteed when no date is set
        res = res.annotate(count=models.Count('load_events_src'))
        res = res.filter(count__gt=0)
        res = res.order_by('-load_events_src__date')
        res = res.first()
        if res is None or len(res.load_events_src.all()) == 0:
            logger.debug('No load events found for Language')
            return None
        return res

    @classmethod
    def get_last_loaded_dst(cls) -> 'Language':
        """Get the last loaded language"""
        res = cls.objects
        # This is not a problem with SQLite, but with postgres, the order is not guaranteed when no date is set
        res = res.annotate(count=models.Count('load_events_dst'))
        res = res.filter(count__gt=0)
        res = res.order_by('-load_events_dst__date')
        res = res.first()
        if res is None or len(res.load_events_dst.all()) == 0:
            logger.debug('No load events found for Language')
            return None
        return res

class LoadEvent(models.Model):
    """Event log for the OCR and translation tasks"""
    description = models.CharField(max_length=512)

    date = models.DateTimeField(auto_now_add=True)

class BaseModel(models.Model):
    """Mixin class for loading entrypoint models"""
    class Meta:
        abstract = True
    # This should be a dict of dicts where the key is the name of the option and the value contains:
    #  - type: The type of the option (str, int, float, bool)
    #  - default: The default value of the option (can be a callable that returns the default value)
    #  - description: A description of the option
    ALLOWED_OPTIONS = {}

    entrypoint_namespace = None

    name = models.CharField(max_length=128)

    entrypoint = models.CharField(max_length=128, null=True)

    language_format = models.CharField(max_length=32, null=True)
    iso1_map = models.JSONField(null=True, blank=True)

    active = models.BooleanField(default=False)

    default_options = models.ForeignKey(
        OptionDict, on_delete=models.SET_NULL, related_name='used_by_%(class)s', null=True
        )

    load_events = models.ManyToManyField(LoadEvent, related_name='%(class)s')

    def __str__(self):
        return str(self.name)

    def __del__(self):
        try:
            self.unload()
        except NotImplementedError:
            pass

    def __getattribute__(self, name):
        res = super().__getattribute__(name)
        if name == 'load':
            def wrapped():
                _res = res()
                self.load_events.create(description=f'Loading model {self.name}')
                return _res
            return wrapped
        return res

    @classmethod
    def get_last_loaded(cls) -> 'BaseModel':
        """Get the last loaded model"""
        res = cls.objects
        res = res.filter(active=True)
        # This is not a problem with SQLite, but with postgres, the order is not guaranteed when no date is set
        res = res.annotate(count=models.Count('load_events'))
        res = res.filter(count__gt=0)
        res = res.order_by('-load_events__date')
        res = res.first()
        if res is None or len(res.load_events.all()) == 0:
            logger.debug(f'No load events found for {cls.__name__}')
            return None
        return res

    def get_lang_code(self, lang: 'Language') -> str:
        """Get the language code for a specific model"""
        if isinstance(self.iso1_map, dict) and lang.iso1 in self.iso1_map:
            return self.iso1_map[lang.iso1]
        return getattr(lang, self.language_format or 'iso1')

    @classmethod
    def from_entrypoint(cls, name: str) -> Type['models.Model']:
        """Get the entrypoint specific TSL model class from the entrypoint name"""
        if cls.entrypoint_namespace is None:
            raise ValueError('Cannot load base model class from entrypoint.')

        obj = cls.objects.get(name=name)
        ept = obj.entrypoint

        logger.debug(f'Loading model {name} from entrypoint {cls.entrypoint_namespace}:{ept}')
        for entrypoint in entry_points(group=cls.entrypoint_namespace, name=ept):
            new_cls = entrypoint.load()
            break
        else:
            raise ValueError(f'Missing plugin: Entrypoint "{ept}" not found.')

        return new_cls.objects.get(name=name)

    def load(self) -> None:
        """Placeholder method for loading the model. To be implemented via entrypoint"""
        raise NotImplementedError('The base model class does not implement this method.')

    def unload(self) -> None:
        """Placeholder method for unloading the model. To be implemented via entrypoint"""
        raise NotImplementedError('The base model class does not implement this method.')

class OCRModel(BaseModel):
    """OCR model."""
    entrypoint_namespace = 'ocr_translate.ocr_models'
    # iso1 code for languages that do not use spaces to separate words
    _NO_SPACE_LANGUAGES = ['ja', 'zh', 'zht', 'lo', 'my']
    _VERTICAL_LANGS = ['ja', 'zh', 'zht', 'ko']
    SINGLE='single'
    MERGED='merged'
    OCR_MODE_CHOICES = [
        (SINGLE, 'Single'),
        (MERGED, 'Merged'),
    ]

    languages = models.ManyToManyField(Language, related_name='ocr_models')
    ocr_mode = models.CharField(max_length=32, choices=OCR_MODE_CHOICES, default=MERGED)
    tokenizer_name = models.CharField(max_length=128, null=True)
    processor_name = models.CharField(max_length=128, null=True)

    def prepare_image(
            self,
            img: PILImage, bbox: tuple[int, int, int, int] = None
            ) -> PILImage:
        """Standard operation to be performed on image before OCR. E.G color scale and crop to bbox"""
        if not isinstance(img, PILImage):
            raise TypeError(f'img should be PIL Image, but got {type(img)}')
        img = img.convert('RGB')

        if bbox:
            img = img.crop(bbox)

        return img

    @staticmethod
    def merge_single_result( # pylint: disable=too-many-locals
            lang: str,
            texts: list[str],
            bboxes_single: list['BBox'],
            bboxes_merged: list['BBox'],
            ) -> list[str]:
        """Merge the results of an OCR run on the single components of a detected bounding box.
        Will try to understand if the text is horizontal or vertical and merge accordingly.

        Args:
            lang (str): Language of the text in iso1 format.
            texts (list[str]): List of texts for each component.
            bboxes_single (list['BBox']): List of single bounding boxes.
            bboxes_merged (list['BBox']): List of merged bounding boxes.

        Returns:
            list[str]: The merged text.
        """
        grouped = {}
        # Group texts and single_bboxes by merged bounding box
        for text, bbox in zip(texts, bboxes_single):
            merged = bbox.to_merged
            ptr = grouped.setdefault(merged, [])
            ptr.append((text, *bbox.lbrt))

        sep = '' if lang in OCRModel._NO_SPACE_LANGUAGES else ' '

        res = []
        for bbox in bboxes_merged:
            single_array = np.array(grouped[bbox], dtype=object)
            l,b,r,t = bbox.lbrt
            width = r - l
            height = t - b

            # Vertical langs can also be written horizontal
            # Assume that if box.width > box.height * 1.3 then it's horizontal
            vertical = lang in OCRModel._VERTICAL_LANGS and height * 1.3 > width

            if vertical:
                # Vertical text find columns
                thr = np.average(single_array[:, 3] - single_array[:, 1]) / 1.5
                centers = (single_array[:, 1] + single_array[:, 3]) / 2
            else:
                # Horizontal text find lines
                thr = np.average(single_array[:, 4] - single_array[:, 2]) / 1.5
                centers = (single_array[:, 2] + single_array[:, 4]) / 2

            # Group lines/cols if the centers are closer than the average line width/height (vertical/non-vert)
            classifiers = np.empty(0)
            line_classifiers = []
            for cen in centers:
                if len(classifiers) == 0:
                    classifiers = np.array([cen])
                    line_classifiers.append(0)
                    continue
                # Index of classifier closest to the center
                i_min = np.argmin(np.abs(classifiers - cen))
                # If the closest classifier is closer than the threshold, reuse it
                if np.abs(classifiers[i_min] - cen) < thr:
                    line_classifiers.append(i_min)
                # Otherwise create a new classifier
                else:
                    classifiers = np.append(classifiers, cen)
                    line_classifiers.append(len(classifiers) - 1)

            line_classifiers = np.array(line_classifiers)
            # Sort lines/cols top-to-bottom or right-to-left
            i_sort = np.argsort(classifiers)[::-1 if vertical else 1]
            text_chunks = []
            # Sort lines/cols chunks left-to-right or top-to-bottom
            sort_col_index = 4 if vertical else 1
            for i in i_sort:
                ind = np.where(line_classifiers == i)[0]
                j_sort = np.argsort(single_array[ind, sort_col_index])
                text_chunks += single_array[ind[j_sort], 0].tolist()

            res.append(sep.join(text_chunks))

        return res

    def _ocr(
            self,
            img: PILImage, lang: str = None, options: dict = None
            ) -> str:
        """PLACEHOLDER (to be implemented via entrypoint): Perform OCR on an image.

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
        # Should return a string with the result of the OCR performed on the input PILImage.
        # Unless the methods `prepare_image` or `ocr` are also being overwritten, the input image will be the
        #  result of the CROP on the original image using the bounding boxes given by the box detection model.
        raise NotImplementedError('The base model class does not implement this method.')

    def ocr(
            self,
            bbox_obj: 'BBox', lang: 'Language',  image: PILImage = None, options: 'OptionDict' = None,
            force: bool = False, block: bool = True,
            ) -> Generator[Union[Message, 'Text'], None, None]:
        """High level function to perform OCR on an image.

        Args:
            bbox_obj (m.BBox): The BBox object from the database.
            lang (m.Language): The Language object from the database.
            image (Image.Image, optional): The image on which to perform OCR. Needed if no previous OCR run exists, or
                force is True.
            options (m.OptionDict, optional): The OptionDict object from the database
                containing the options for the OCR.
            force (bool, optional): Whether to force the OCR to run again even if a previous run exists.
                Defaults to False.
            block (bool, optional): Whether to block until the task is complete. Defaults to True.

        Raises:
            ValueError: ValueError is raised if at any step of the pipeline an image is required but not provided.

        Yields:
            Generator[Union[Message, m.Text], None, None]:
                If block is False, yields a Message object for the OCR run first and the resulting Text object second.
                If block is True, yields the resulting Text object.
        """
        options_obj = options
        if options_obj is None:
            options_obj = OptionDict.objects.get(options={})
        params = {
            'bbox': bbox_obj,
            'model': self,
            'lang_src': lang,
            'options': options_obj,
        }
        ocr_run_obj = OCRRun.objects.filter(**params).first()
        if ocr_run_obj is None or force:
            if image is None:
                raise ValueError('Image is required for OCR')
            logger.info('Running OCR')

            id_ = (bbox_obj.id, self.id, lang.id, options_obj.id)
            mlang = self.get_lang_code(lang)
            opt_dct = options_obj.options
            text = queues.ocr_queue.put(
                id_=id_,
                handler=self._ocr,
                msg={
                    'args': (self.prepare_image(image, bbox_obj.lbrt),),
                    'kwargs': {
                        'lang': mlang,
                        'options': opt_dct
                        },
                },
            )
            if not block:
                yield text
            text = text.response()
            if lang.iso1 in self._NO_SPACE_LANGUAGES:
                text = text.replace(' ', '')

            text_obj = get_or_create(Text, text=text)
            params[f'result_{self.ocr_mode}'] = text_obj
            ocr_run_obj = OCRRun.objects.create(**params)
        else:
            if not block:
                # Both branches should have the same number of yields
                yield None
            logger.info(f'Reusing OCR <{ocr_run_obj.id}>')
            # It is possible that single has to be performed is a previous pipeline was interrupted
            text_obj = ocr_run_obj.result_merged or ocr_run_obj.result_single
            # text = ocr_run.result.text

        yield text_obj


class BoxDetectionResult(TypedDict):
    """Type for the result of the box detection"""
    single: list[tuple[int, int, int, int]]
    merged: tuple[int, int, int, int]

class OCRBoxModel(BaseModel):
    """OCR model for bounding boxes"""
    #pylint: disable=abstract-method
    entrypoint_namespace = 'ocr_translate.box_models'

    languages = models.ManyToManyField(Language, related_name='box_models')

    def _box_detection(
            self,
            image: PILImage, options: dict = None
            ) -> list[BoxDetectionResult]:
        """PLACEHOLDER (to be implemented via entrypoint): Perform box OCR on an image.
        Returns list of bounding boxes as dicts:
            - merged: The merged BBox as a tuple[int, int, int, int]
            - single: List of BBoxed merged into the merged BBox as a tuple[int, int, int, int]

        Args:
            image (Image.Image): A Pillow image on which to perform OCR.
            options (dict, optional): A dictionary of options.

        Raises:
            NotImplementedError: The type of model specified is not implemented.

        Returns:
            list[BoxDetectionResult]: List of dictionary with key/value pairs:
              - merged: The merged BBox as a tuple[int, int, int, int]
              - single: List of BBoxed merged into the merged BBox as a tuple[int, int, int, int]
        """
        # Redefine this method with the same signature as above
        # Should return a list of `lrbt` boxes after processing the input PILImage
        raise NotImplementedError('The base model class does not implement this method.')

    def box_detection( # pylint: disable=too-many-locals
            self,
            img_obj: 'Image', lang: 'Language', image: PILImage = None,
            force: bool = False, options: 'OptionDict' = None
            ) -> tuple[list['BBox'], list['BBox']]:
        """High level function to perform box OCR on an image. Will attempt to reuse a previous run if possible.

        Args:
            img_obj (m.Image): An Image object from the database.
            lang (m.Language): A Language object from the database (not every model is gonna use this).
            image (Image.Image, optional): The Pillow image to be used for OCR if a previous result is not found.
                Defaults to None.
            force (bool, optional): If true, re-run the OCR even if a previous result is found. Defaults to False.
            options (m.OptionDict, optional): An OptionDict object from the database. Defaults to None.

        Raises:
            ValueError: ValueError is raised if at any step of the pipeline an image is required but not provided.

        Returns:
            tuple[list['BBox'], list['BBox']]: Tuple of lists of BBox objects from the database.
                First list is the single bounding boxes, second list is the merged bounding boxes.
        """
        options_obj = options or OptionDict.objects.get(options={})
        params = {
            'image': img_obj,
            'model': self,
            'options': options_obj,
            'lang_src': lang,
        }

        bbox_run = OCRBoxRun.objects.filter(**params).first()
        # Needed to rerun the OCR from <0.4.x to >=0.4.x
        # Before only merged boxes where saved, now also the single are needed
        if isinstance(bbox_run, OCRBoxRun):
            if len(bbox_run.result_single.all()) == 0 and len(bbox_run.result_merged.all()) > 0:
                bbox_run.delete()
                bbox_run = None
        if bbox_run is None or force:
            if image is None:
                raise ValueError('Image is required for BBox OCR')
            logger.info('Running BBox OCR')
            opt_dct = options_obj.options
            id_ = (img_obj.id, self.id, lang.id, options_obj.id)
            bboxes = queues.box_queue.put(
                id_=id_,
                handler=self._box_detection,
                msg={
                    'args': (image,),
                    'kwargs': {'options': opt_dct},
                },
            )
            # bboxes_single, bboxes_merged = bboxes.response()
            bboxes_list = bboxes.response()
            # Create it here to avoid having a failed entry in DB
            bbox_run = OCRBoxRun.objects.create(**params)
            for dct in bboxes_list:
                merged = dct['merged']
                l,b,r,t = merged
                bbox_merged_obj = BBox.objects.create(
                    l=l, b=b, r=r, t=t,
                    image=img_obj,
                    from_ocr_merged=bbox_run,
                    )
                for bbox in dct['single']:
                    l,b,r,t = bbox
                    BBox.objects.create(
                        l=l, b=b, r=r, t=t,
                        image=img_obj,
                        from_ocr_single=bbox_run,
                        to_merged=bbox_merged_obj,
                        )
        else:
            logger.info(f'Reusing BBox OCR <{bbox_run.id}>')

        res_single = list(bbox_run.result_single.all())
        res_merged = list(bbox_run.result_merged.all())
        logger.debug(f'BBox OCR result: {len(res_single)} single boxes')
        logger.info(f'BBox OCR result: {len(res_merged)} merged boxes')

        return res_single, res_merged


class TSLModel(BaseModel):
    """Translation models using hugging space naming convention"""
    ALLOWED_OPTIONS = {
        'ignore_chars': {
            'type': str,
            'default': ('cascade', ['lang_src', 'tsl_model'], ''),
            'description': 'Characters to ignore during translation.',
        },
        'break_chars': {
            'type': str,
            'default': ('cascade', ['lang_src', 'tsl_model'], ''),
            'description': (
                'Characters on which lines will be split for translation.\n'
                'The split lines are translated separately (no context between them) and then merged back together.)'
                ),
        },
        'allowed_start_end': {
            'type': str,
            'default': ('cascade', ['lang_src', 'tsl_model'], ''),
            'description': (
                'Characters allowed at the start and end of a line.\n'
                'Some models like tesseract, will detect the edges of text bubbles as text and spit out garbage '
                'at the start/end of the translated line. This option will filter out any caracter that is not '
                'allowed at the start/end of a line.'
                ),
        },
        'break_newlines': {
            'type': bool,
            'default': ('cascade', ['lang_src', 'tsl_model'], False),
            'description': 'Split lines on newlines. If false the newlines will be replaced with spaces.',
        },
        'restore_missing_spaces': {
            'type': bool,
            'default': ('cascade', ['lang_src', 'tsl_model'], False),
            'description': (
                'Some models will OCR text without spaces between some of the words.\n'
                'This option will attempt to restore the missing spaces by finding the shortest valid decomposition '
                'also keeping into account the word frequency.\n'
                '(Only available if a trie is loaded for the source language.)'
                ),
        },
        'restore_dash_newlines': {
            'type': bool,
            'default': ('cascade', ['lang_src', 'tsl_model'], False),
            'description': (
                'Text can be written with dash splitting a word onto a new line.\n'
                'If this option is enabled, dashes preceded by a character and followed by a newline will be removed '
                'togheter with the newline to merge the word back together.'
                ),
        },
    }
    entrypoint_namespace = 'ocr_translate.tsl_models'

    src_languages = models.ManyToManyField(Language, related_name='tsl_models_src')
    dst_languages = models.ManyToManyField(Language, related_name='tsl_models_dst')

    @staticmethod
    def pre_tokenize( # pylint: disable=too-many-branches
            text: str,
            ignore_chars: str = None,
            break_chars: str = None,
            allowed_start_end: str = None,
            break_newlines: bool = False,
            restore_missing_spaces: bool = False,
            restore_dash_newlines: bool = False,
            **kwargs
            ) -> list[str]:
        """Pre-tokenize a text string.

        Args:
            text (str): Text to tokenize.
            lang (str): Language of the text.
            ignore_chars (str, optional): String of characters to ignore. Defaults to None.
            break_chars (str, optional): String of characters to break on. Defaults to None.
            allowed_start_end (str, optional): String of characters allowed at the start and end of a line.
            break_newlines (bool, optional): Whether to break on newlines. Defaults to True.
            restore_missing_spaces (bool, optional): Whether to restore missing spaces (2 word with no space between).
            restore_dash_newlines (bool, optional): Whether to restore dash-newlines (word broken with a -newline).
                Defaults to False.

        Returns:
            list[str]: List of string tokens.
        """
        if isinstance(break_newlines, str):
            break_newlines = break_newlines.lower() == 'true'
        if isinstance(restore_missing_spaces, str):
            restore_missing_spaces = restore_missing_spaces.lower() == 'true'
        if isinstance(restore_dash_newlines, str):
            restore_dash_newlines = restore_dash_newlines.lower() == 'true'
        orig_text = text
        if allowed_start_end is not None:
            rgx_start = re.compile(
                '(?x)'
                rf'^[^{allowed_start_end}]+\S?(?= )'
                '|'
                rf'^\S[^{allowed_start_end}]+(?= )'
                )

            rgx_end = re.compile(
                '(?x)'
                rf'(?<= )\S?[^{allowed_start_end}]+$'
                '|'
                rf'(?<= )[^{allowed_start_end}]+\S$'
                )

            app = []
            for split in text.split('\n'):
                split = rgx_start.sub('', split)
                split = rgx_end.sub('', split)
                app.append(split)
            text = '\n'.join(app)
        if restore_dash_newlines:
            text = re.sub(r'(?<!\n)- *\n', '', text)
        if ignore_chars:
            text = re.sub(f'[{ignore_chars}]+', '', text)
        if break_chars is None:
            break_chars = ''
        if break_newlines:
            break_chars += '\n'
        else:
            text = text.replace('\n', ' ')

        if restore_missing_spaces and not (trie := get_trie_src()) is None:
            res = [
                trie.decompose(split, min_length=1)
                if not trie.search(split, strict=False) else
                [[split]]
                for split in text.lower().split(' ')
                ]

            # Use a list of word frequencies to determine the best split
            def sum_freq(lst: list) -> float:
                return sum(trie.get_freq(w) for w in lst) / len(lst)**4.0

            res = [' '.join(max(_, key=sum_freq)) for _ in filter(None, res)]
            text = ' '.join(res)

        break_chars = re.escape(break_chars)
        tokens = text
        if len(break_chars) > 0:
            tokens = re.split(f'[{break_chars}+]', text)

        if isinstance(tokens, str):
            tokens = [text]

        res = list(filter(None, tokens))
        logger.debug(f'Pre-tokenized "{orig_text}" to {res}')
        return res if len(res) > 0 else [' ']


    def _translate(
            self,
            tokens: list, src_lang: str, dst_lang: str, options: dict = None) -> str | list[str]:
        """PLACEHOLDER (to be implemented via entrypoint): Translate a text using a the loaded model.

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
        # Should return a string with the translated text.
        # IMPORTANT: the main codebase treats this function as batchable:
        # The input `tokens` can be a list of strings or a list of list of strings. The output should match the input
        #   being a string or list of strings.
        # (This is used to leverage the capability of pytorch to batch inputs and outputs for faster performances,
        #   or it can also used to write a plugin for an online service by using a single request for multiple inputs
        #   using some separator that the service will leave unaltered.)
        raise NotImplementedError('The base model class does not implement this method.')

    def find_manual(self,  text_obj: 'Text', src: 'Language', dst: 'Language') -> 'TranslationRun':
        """Find a manual translation run for the given text with the specified source and destination languages.
        Args:
            text_obj (m.Text): Text object from the database to translate.
            src (m.Language): Source language object from the database.
            dst (m.Language): Destination language object from the database.

        Returns:
            m.TranslationRun: The TranslationRun object from the database.
        """
        manual_model, _ = TSLModel.objects.get_or_create(name='manual')
        params = {
            'model': manual_model,
            'lang_src': src,
            'lang_dst': dst,
            'text': text_obj,
            'options': OptionDict.objects.get(options={})
        }
        # logger.debug(f'Looking for manual TSL with params: {params}')
        return TranslationRun.objects.filter(**params).first()


    def translate(
            self,
            text_obj: 'Text', src: 'Language', dst: 'Language', options: 'OptionDict' = None,
            force: bool = False,
            block: bool = True,
            favor_manual: bool = True,
            lazy: bool = False
            ) -> Generator[Union[Message, 'Text'], None, None]:
        """High level translate call generating a TranslationRun entry.
        Args:
            text_obj (m.Text): Text object from the database to translate.
            src (m.Language): Source language object from the database.
            dst (m.Language): Destination language object from the database.
            options (m.OptionDict, optional): OptionDict object from the database. Defaults to None.
            force (bool, optional): Whether to force a new TSL run. Defaults to False.
            block (bool, optional): Whether to block until the task is complete. Defaults to True.
            favor_manual (bool, optional): Whether to favor manual translations over TSL. Defaults to True.
            lazy (bool, optional): Whether to raise an error if the TSL run is not found. Defaults to False.

        Raises:
            ValueError: If lazy and force are both True or if lazy is True and the TSL run is not found.

        Yields:
            Generator[Union[Message, m.Text], None, None]:
                If block is False, yields a Message object for the TSL run first and the resulting Text object second.
                If block is True, yields the resulting Text object.
        """
        if lazy and force:
            raise ValueError('Cannot force + lazy TSL run')
        # Check if a ManualModel is being used
        tsl_run_obj = None
        if favor_manual:
            tsl_run_obj = self.find_manual(text_obj, src, dst)
        if tsl_run_obj is None:
            options_obj = options or OptionDict.objects.get(options={})
            params = {
                'options': options_obj,
                'text': text_obj,
                'model': self,
                'lang_src': src,
                'lang_dst': dst,
            }
            tsl_run_obj = TranslationRun.objects.filter(**params).first()
        if tsl_run_obj is None or force:
            if lazy:
                raise ValueError('Value not found for lazy TSL run')
            logger.info('Running TSL')
            # Generate a unique id for a message
            id_ = (text_obj.id, self.id, options_obj.id, src.id, dst.id, options_obj.id)
            batch_id = (self.id, options_obj.id, src.id, dst.id, options_obj.id)
            lang_dct = getattr(src.default_options, 'options', {})
            model_dct =  getattr(self.default_options, 'options', {})
            opt_dct = {**lang_dct, **model_dct, **options_obj.options}

            tokens = self.pre_tokenize(text_obj.text, **opt_dct)
            new = queues.tsl_queue.put(
                id_=id_,
                batch_id=batch_id,
                handler=self._translate,
                msg={
                    'args': (
                        tokens,
                        self.get_lang_code(src),
                        self.get_lang_code(dst),
                        ),
                    'kwargs': {'options': opt_dct},
                },
            )
            if not block:
                yield new
            new = new.response()
            text_obj = get_or_create(Text, text=new)
            params['result'] = text_obj
            tsl_run_obj = TranslationRun.objects.create(**params)
        else:
            if not block:
                # Both branches should have the same number of yields
                yield None
            manual = ''
            if tsl_run_obj.model.name == 'manual':
                manual = 'manual '
            logger.info(f'Reusing {manual}TSL <{tsl_run_obj.id}>')

        yield tsl_run_obj.result

class Image(models.Model):
    """Image registered as the md5 of the uploaded file"""
    md5 = models.CharField(max_length=32, unique=True)

class BBox(models.Model):
    """Bounding box of a text in an image"""
    l = models.IntegerField(null=False)
    b = models.IntegerField(null=False)
    r = models.IntegerField(null=False)
    t = models.IntegerField(null=False)

    image = models.ForeignKey(Image, on_delete=models.CASCADE, related_name='bboxes')
    from_ocr_single = models.ForeignKey(
        'OCRBoxRun', on_delete=models.CASCADE, related_name='result_single',
        default=None, null=True
        )
    from_ocr_merged = models.ForeignKey(
        'OCRBoxRun', on_delete=models.CASCADE, related_name='result_merged',
        default=None, null=True
        )
    to_merged = models.ForeignKey(
        'BBox', on_delete=models.CASCADE, related_name='from_single',
        default=None, null=True
        )

    @property
    def lbrt(self):
        """Return the bounding box as a tuple of (left, bottom, right, top)"""
        return self.l, self.b, self.r, self.t

    def __str__(self):
        return f'{self.lbrt}'

class Text(models.Model):
    """Text extracted from an image or translated from another text"""
    text = models.TextField()
    # lang = models.ForeignKey(Language, on_delete=models.CASCADE, related_name='texts')

class OCRBoxRun(models.Model):
    """OCR run on an image using a specific model"""
    options = models.ForeignKey(OptionDict, on_delete=models.CASCADE, related_name='ocr_box_options')

    lang_src = models.ForeignKey(Language, on_delete=models.CASCADE, related_name='box_src')

    image = models.ForeignKey(Image, on_delete=models.CASCADE, related_name='to_box')
    model = models.ForeignKey(OCRBoxModel, on_delete=models.CASCADE, related_name='box_runs')
    # result = models.ForeignKey(BBox, on_delete=models.CASCADE, related_name='from_ocr')

class OCRRun(models.Model):
    """OCR run on an image using a specific model"""
    options = models.ForeignKey(OptionDict, on_delete=models.CASCADE, related_name='ocr_options')

    lang_src = models.ForeignKey(Language, on_delete=models.CASCADE, related_name='ocr_src')

    # image = models.ForeignKey(Image, on_delete=models.CASCADE, related_name='to_ocr')
    bbox = models.ForeignKey(BBox, on_delete=models.CASCADE, related_name='to_ocr')
    model = models.ForeignKey(OCRModel, on_delete=models.CASCADE, related_name='ocr_runs')
    result_single = models.ForeignKey(
        Text, on_delete=models.CASCADE, related_name='from_ocr_single',
        default=None, null=True
        )
    result_merged = models.ForeignKey(
        Text, on_delete=models.CASCADE, related_name='from_ocr_merged',
        default=None, null=True
        )

class TranslationRun(models.Model):
    """Translation run on a text using a specific model"""
    options = models.ForeignKey(OptionDict, on_delete=models.CASCADE, related_name='trans_options')

    lang_src = models.ForeignKey(Language, on_delete=models.CASCADE, related_name='trans_src')
    lang_dst = models.ForeignKey(Language, on_delete=models.CASCADE, related_name='trans_dst')

    text = models.ForeignKey(Text, on_delete=models.CASCADE, related_name='to_trans')
    model = models.ForeignKey(TSLModel, on_delete=models.CASCADE, related_name='tsl_runs')
    result = models.ForeignKey(Text, on_delete=models.CASCADE, related_name='from_trans')
