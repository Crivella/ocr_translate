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
from typing import Generator, Union

import numpy as np
from django.db import models
from PIL.Image import Image as PILImage

from .. import queues
from ..messaging import Message
from .base import BaseModel, Language, OptionDict, Text, safe_get_or_create
from .box import BBox

logger = logging.getLogger('ocr.general')

class OCRModel(BaseModel):
    """OCR model."""
    CREATE_LANG_KEYS = {'lang': 'languages'}

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

            text_obj = safe_get_or_create(Text, text=text)
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
