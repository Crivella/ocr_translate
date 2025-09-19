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
from typing import TypedDict

from django.db import models
from PIL.Image import Image as PILImage

from .. import queues
from .base import BaseModel, Image, Language, OptionDict

logger = logging.getLogger('ocr.general')


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

class BoxDetectionResult(TypedDict):
    """Type for the result of the box detection"""
    single: list[tuple[int, int, int, int]]
    merged: tuple[int, int, int, int]


class OCRBoxModel(BaseModel):
    """OCR model for bounding boxes"""
    #pylint: disable=abstract-method
    CREATE_LANG_KEYS = {'lang': 'languages'}

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


class OCRBoxRun(models.Model):
    """OCR run on an image using a specific model"""
    options = models.ForeignKey(OptionDict, on_delete=models.CASCADE, related_name='ocr_box_options')

    lang_src = models.ForeignKey(Language, on_delete=models.CASCADE, related_name='box_src')

    image = models.ForeignKey(Image, on_delete=models.CASCADE, related_name='to_box')
    model = models.ForeignKey(OCRBoxModel, on_delete=models.CASCADE, related_name='box_runs')
    # result = models.ForeignKey(BBox, on_delete=models.CASCADE, related_name='from_ocr')
