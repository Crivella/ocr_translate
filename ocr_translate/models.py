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
from typing import Generator, Type, Union

from django.db import models
from PIL.Image import Image as PILImage

from . import queues
from .messaging import Message
from .tries import get_trie_src

logger = logging.getLogger('ocr.general')

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

    def __str__(self):
        return str(self.iso1)

class BaseModel(models.Model):
    """Mixin class for loading entrypoint models"""
    class Meta:
        abstract = True

    entrypoint_namespace = None

    name = models.CharField(max_length=128)

    entrypoint = models.CharField(max_length=128, null=True)

    language_format = models.CharField(max_length=32, null=True)
    iso1_map = models.JSONField(null=True)

    default_options = models.ForeignKey(
        OptionDict, on_delete=models.SET_NULL, related_name='used_by_%(class)s', null=True
        )

    def __str__(self):
        return str(self.name)

    def __del__(self):
        try:
            self.unload()
        except NotImplementedError:
            pass

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
    NO_SPACE_LANGUAGES = ['ja', 'zh', 'lo', 'my']

    languages = models.ManyToManyField(Language, related_name='ocr_models')

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

    def _ocr(
            self,
            img: PILImage, lang: str = None, options: dict = None
            ) -> str:
        """Placeholder method for performing OCR. To be implemented via entrypoint"""
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
                If block is True, yields a Message object for the OCR run first and the resulting Text object second.
                If block is False, yields the resulting Text object.
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

            id_ = (bbox_obj.id, self.id, lang.id)
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
            if lang.iso1 in self.NO_SPACE_LANGUAGES:
                text = text.replace(' ', '')
            text_obj, _ = Text.objects.get_or_create(
                text=text,
                )
            params['result'] = text_obj
            ocr_run_obj = OCRRun.objects.create(**params)
        else:
            if not block:
                # Both branches should have the same number of yields
                yield None
            logger.info(f'Reusing OCR <{ocr_run_obj.id}>')
            text_obj = ocr_run_obj.result
            # text = ocr_run.result.text

        yield text_obj


class OCRBoxModel(BaseModel):
    """OCR model for bounding boxes"""
    #pylint: disable=abstract-method
    entrypoint_namespace = 'ocr_translate.box_models'

    languages = models.ManyToManyField(Language, related_name='box_models')

    def _box_detection(
            self,
            image: PILImage, options: dict = None
            ) -> list[tuple[int, int, int, int]]:
        """Placeholder method for performing box detection. To be implemented via entrypoint"""
        raise NotImplementedError('The base model class does not implement this method.')

    def box_detection(
            self,
            img_obj: 'Image', lang: 'Language', image: PILImage = None,
            force: bool = False, options: 'OptionDict' = None
            ) -> list['BBox']:
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
            list[m.BBox]: A list of BBox objects containing the resulting bounding boxes.
        """
        options_obj = options or OptionDict.objects.get(options={})
        params = {
            'image': img_obj,
            'model': self,
            'options': options_obj,
            'lang_src': lang,
        }

        bbox_run = OCRBoxRun.objects.filter(**params).first()
        if bbox_run is None or force:
            if image is None:
                raise ValueError('Image is required for BBox OCR')
            logger.info('Running BBox OCR')
            opt_dct = options_obj.options
            id_ = (img_obj.id, self.id, lang.id)
            bboxes = queues.box_queue.put(
                id_=id_,
                handler=self._box_detection,
                msg={
                    'args': (image,),
                    'kwargs': {'options': opt_dct},
                },
            )
            bboxes = bboxes.response()
            # Create it here to avoid having a failed entry in DB
            bbox_run = OCRBoxRun.objects.create(**params)
            for bbox in bboxes:
                l,b,r,t = bbox
                BBox.objects.create(
                    l=l,
                    b=b,
                    r=r,
                    t=t,
                    image=img_obj,
                    from_ocr=bbox_run,
                    )
        else:
            logger.info(f'Reusing BBox OCR <{bbox_run.id}>')
        logger.info(f'BBox OCR result: {len(bbox_run.result.all())} boxes')

        return list(bbox_run.result.all())


class TSLModel(BaseModel):
    """Translation models using hugging space naming convention"""
    entrypoint_namespace = 'ocr_translate.tsl_models'

    src_languages = models.ManyToManyField(Language, related_name='tsl_models_src')
    dst_languages = models.ManyToManyField(Language, related_name='tsl_models_dst')

    @staticmethod
    def pre_tokenize(
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
            break_newlines (bool, optional): Whether to break on newlines. Defaults to True.
            restore_missing_spaces (bool, optional): Whether to restore missing spaces (2 word with no space between).
            restore_dash_newlines (bool, optional): Whether to restore dash-newlines (word broken with a -newline).
                Defaults to False.

        Returns:
            list[str]: List of string tokens.
        """
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
        if ignore_chars is not None:
            text = re.sub(f'[{ignore_chars}]+', '', text)
        if break_chars is None:
            break_chars = ''
        if break_newlines:
            break_chars += '\n'
        else:
            text = text.replace('\n', ' ')

        if restore_missing_spaces:
            trie = get_trie_src()

            res = [
                trie.decompose(split, min_length=1)
                if not trie.search(split, strict=False) else
                [[split]]
                for split in text.lower().split(' ')
                ]

            # Use a list of word frequencies to determine the best split
            def sum_freq(lst: list) -> float:
                return sum(trie.get_freq(w) for w in lst) / len(lst)**1.5

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


    def _translate(self, tokens: list, src_lang: str, dst_lang: str, options: dict = None) -> str | list[str]:
        """Placeholder method for translating a text. To be implemented via entrypoint"""
        raise NotImplementedError('The base model class does not implement this method.')

    def translate(
            self,
            text_obj: 'Text', src: 'Language', dst: 'Language', options: 'OptionDict' = None,
            force: bool = False,
            block: bool = True,
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
            lazy (bool, optional): Whether to raise an error if the TSL run is not found. Defaults to False.

        Raises:
            ValueError: If lazy and force are both True or if lazy is True and the TSL run is not found.

        Yields:
            Generator[Union[Message, m.Text], None, None]:
                If block is True, yields a Message object for the TSL run first and the resulting Text object second.
                If block is False, yields the resulting Text object.
        """
        if lazy and force:
            raise ValueError('Cannot force + lazy TSL run')
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
            id_ = (text_obj.id, self.id, options_obj.id, src.id, dst.id)
            batch_id = (self.id, options_obj.id, src.id, dst.id)
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
            text_obj, _ = Text.objects.get_or_create(
                text = new,
                )
            params['result'] = text_obj
            tsl_run_obj = TranslationRun.objects.create(**params)
        else:
            if not block:
                # Both branches should have the same number of yields
                yield None
            logger.info(f'Reusing TSL <{tsl_run_obj.id}>')

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
    from_ocr = models.ForeignKey('OCRBoxRun', on_delete=models.CASCADE, related_name='result')

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
    result = models.ForeignKey(Text, on_delete=models.CASCADE, related_name='from_ocr')

class TranslationRun(models.Model):
    """Translation run on a text using a specific model"""
    options = models.ForeignKey(OptionDict, on_delete=models.CASCADE, related_name='trans_options')

    lang_src = models.ForeignKey(Language, on_delete=models.CASCADE, related_name='trans_src')
    lang_dst = models.ForeignKey(Language, on_delete=models.CASCADE, related_name='trans_dst')

    text = models.ForeignKey(Text, on_delete=models.CASCADE, related_name='to_trans')
    model = models.ForeignKey(TSLModel, on_delete=models.CASCADE, related_name='tsl_runs')
    result = models.ForeignKey(Text, on_delete=models.CASCADE, related_name='from_trans')
