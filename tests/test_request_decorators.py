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
"""Tests for request decorators."""

import threading
import time

import pytest
from django.http import JsonResponse

from ocr_translate import request_decorators as rd


@pytest.fixture(autouse=True)
def clear_locks():
    """Clear locks before and after each test."""
    yield
    rd.locks.clear()


def test_use_lock_same():
    """Test two functions with the same lock."""
    res = []
    @rd.use_lock('test', blocking=True)
    def long():
        """Test function 1."""
        time.sleep(.5)
        res.append('long')

    @rd.use_lock('test', blocking=True)
    def short():
        """Test function 2."""
        res.append('short')

    t1 = threading.Thread(target=long)
    t2 = threading.Thread(target=short)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    assert res == ['long', 'short']
    assert 'test' in rd.locks

def test_use_lock_nonblocking_norelease():
    """Test that a nonblocking use does not release if the lock was not acquired."""
    res = []
    @rd.use_lock('test', blocking=True)
    def long():
        """Test function 1."""
        time.sleep(.5)
        res.append('long')

    @rd.use_lock('test', blocking=False)
    def short():
        """Test function 2."""
        res.append('short')

    t1 = threading.Thread(target=long)
    t2 = threading.Thread(target=short)
    t1.start()
    t2.start()
    t2.join()
    assert 'test' in rd.locks
    assert rd.locks['test'].locked()
    t1.join()
    assert res == ['short', 'long']

def test_use_lock_nonblocking_acquire():
    """Test that a nonblocking use acquires the lock."""
    res = []
    @rd.use_lock('test', blocking=False)
    def long():
        """Test function 1."""
        time.sleep(.5)
        res.append('long')

    @rd.use_lock('test', blocking=True)
    def short():
        """Test function 2."""
        res.append('short')

    t1 = threading.Thread(target=long)
    t2 = threading.Thread(target=short)
    t1.start()
    assert 'test' in rd.locks
    assert rd.locks['test'].locked()
    t2.start()
    t2.join()
    t1.join()
    assert res == ['long', 'short']

def test_use_lock_different():
    """Test two functions with different lock."""
    res = []
    @rd.use_lock('test1')
    def long():
        """Test function 1."""
        time.sleep(.5)
        res.append('long')

    @rd.use_lock('test2')
    def short():
        """Test function 2."""
        res.append('short')

    t1 = threading.Thread(target=long)
    t2 = threading.Thread(target=short)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    assert res == ['short', 'long']
    assert 'test1' in rd.locks
    assert 'test2' in rd.locks

def test_wait_for_lock_nonexisting():
    """Test wait_for_lock does not wait for non_existing lock."""
    res = []
    assert 'test' not in rd.locks
    @rd.wait_for_lock('test')
    def short():
        """Test function 2."""
        res.append('short')

    t = threading.Thread(target=short)
    t.start()
    t.join(timeout=1)


def test_wait_for_existing_lock():
    """Test wait_for_lock does not wait for existing lock."""
    res = []
    @rd.use_lock('test')
    def long():
        """Test function 1."""
        time.sleep(.5)
        res.append('long')

    @rd.wait_for_lock('test')
    def short():
        """Test function 2."""
        res.append('short')

    t1 = threading.Thread(target=long)
    t2 = threading.Thread(target=short)
    t1.start()
    t2.start()
    t1.join()
    t2.join(timeout=2)

    assert res == ['long', 'short']


def test_wait_for_existing_lock_timeout():
    """Test wait_for_lock does not wait for existing lock timing out."""
    @rd.use_lock('test')
    def long():
        """Test function 1."""
        time.sleep(2)

    @rd.wait_for_lock('test', timeout=.1)
    def short():
        """Test function 2."""
        return 1

    res = None
    def save_result():
        nonlocal res
        res = short()

    t1 = threading.Thread(target=long)
    t2 = threading.Thread(target=save_result)
    t1.start()
    t2.start()
    t2.join(timeout=2)
    assert isinstance(res, JsonResponse)
