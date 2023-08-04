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
"""OCRtranslate plugin to allow usage of easyocr."""

import logging
from typing import Iterable

import easyocr
import numpy as np
import torch
from PIL.Image import Image as PILImage

from ocr_translate import models as m

logger = logging.getLogger('plugin')

class EasyOCRBoxModel(m.OCRBoxModel):
    """OCRtranslate plugin to allow usage of easyocr for box detection."""
    class Meta:
        proxy = True

    def __init__(self, *args, **kwargs):
        """Initialize the model."""
        super().__init__(*args, **kwargs)

        self.reader = None
        self.dev = 'cpu'

    def load(self):
        """Load the model into memory."""
        logger.info(f'Loading BOX model: {self.name}')
        self.reader = easyocr.Reader([], gpu=(self.dev == 'cuda'), recognizer=False)

    def unload(self) -> None:
        """Unload the model from memory."""
        if self.reader is not None:
            del self.reader
            self.reader = None

        if self.dev == 'cuda':
            torch.cuda.empty_cache()

    @staticmethod
    def intersections(bboxes: Iterable[tuple[int, int, int, int]], margin: int = 5) -> list[set[int]]:
        """Determine the intersections between a list of bounding boxes.

        Args:
            bboxes (Iterable[tuple[int, int, int, int]]): List of bounding boxes in lrbt format.
            margin (int, optional): Number of extra pixels outside of the boxes that define an intersection.
                Defaults to 5.

        Returns:
            list[set[int]]: List of sets of indexes of the boxes that intersect.
        """
        res = []

        for i,(l1,r1,b1,t1) in enumerate(bboxes):
            l1 -= margin
            r1 += margin
            b1 -= margin
            t1 += margin

            for j,(l2,r2,b2,t2) in enumerate(bboxes):
                if i == j:
                    continue

                if l1 >= r2 or r1 <= l2 or b1 >= t2 or t1 <= b2:
                    continue

                for ptr in res:
                    if i in ptr or j in ptr:
                        break
                else:
                    ptr = set()
                    res.append(ptr)

                ptr.add(i)
                ptr.add(j)

        return res

    @staticmethod
    def merge_bboxes(bboxes: Iterable[tuple[int, int, int, int]]) -> list[tuple[int, int, int, int]]:
        """Merge a list of intersecting bounding boxes. All intersecting boxes are merged into a single box.

        Args:
            bboxes (Iterable[Iterable[int]]): Iterable of bounding boxes in lrbt format.

        Returns:
            list[tuple[int]]: List of merged bounding boxes in lrbt format.
        """
        res = []
        bboxes = np.array(bboxes)
        inters = EasyOCRBoxModel.intersections(bboxes)

        lst = list(range(len(bboxes)))

        torm = set()
        for app in inters:
            app = list(app)
            data = bboxes[app].reshape(-1,4)
            l = data[:,0].min()
            r = data[:,1].max()
            b = data[:,2].min()
            t = data[:,3].max()

            res.append([l,b,r,t])

            torm = torm.union(app)

        for i in lst:
            if i in torm:
                continue
            l,r,b,t = bboxes[i]
            res.append([l,b,r,t])

        return res

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

        if options is None:
            options = {}

        # reader.recognize(image)
        image = image.convert('RGB')
        results = self.reader.detect(np.array(image))

        # Axis rectangles
        bboxes = results[0][0]

        # Free (NOT IMPLEMENTED)
        # ...

        bboxes = self.merge_bboxes(bboxes)

        return bboxes
