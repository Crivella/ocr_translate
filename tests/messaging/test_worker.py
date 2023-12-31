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
"""Tests for messaging.py"""
# pylint: disable=redefined-outer-name

import queue
import threading

from ocr_translate.messaging import Worker


def test_worker_instantiation(worker):
    """Test that the worker class can be instantiated"""
    assert isinstance(worker, Worker)
    assert isinstance(worker.queue, queue.SimpleQueue)

def test_worker_start(worker):
    """Test that the worker class can be started"""
    assert worker.thread is None
    worker.start()
    assert isinstance(worker.thread, threading.Thread)
    assert worker.thread.is_alive()

def test_worker_stop(worker):
    """Test that the worker class can be stopped"""
    worker.start()
    worker.stop()
    assert not worker.thread.is_alive()
