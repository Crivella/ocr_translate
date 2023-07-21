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
"""Queues definition for the ocr_translate app."""
import os

from .messaging import WorkerMessageQueue

num_main_workers = int(os.environ.get('NUM_MAIN_WORKERS', 4))
num_box_workers = int(os.environ.get('NUM_BOX_WORKERS', 1))
num_ocr_workers = int(os.environ.get('NUM_OCR_WORKERS', 1))
num_tsl_workers = int(os.environ.get('NUM_TSL_WORKERS', 1))

main_queue = WorkerMessageQueue(num_workers=num_main_workers)
box_queue = WorkerMessageQueue(num_workers=num_box_workers)
ocr_queue = WorkerMessageQueue(num_workers=num_ocr_workers)
tsl_queue = WorkerMessageQueue(
    num_workers=num_tsl_workers,
    allow_batching=True,
    # batch_timeout=15,
    batch_args= (0,)
    )

main_queue.start_workers()
box_queue.start_workers()
ocr_queue.start_workers()
tsl_queue.start_workers()
