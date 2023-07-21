"""Fixtures for ocr_tsl tests"""

import pytest

strings = [
    'This is a test string.',
    'This is a test string.\nWith a newline.',
    'This is a test string.\nWith a newline.\nAnd another.',
    'This is a test string.? With a special break character.',
    'This is a test string.? With a special break character.\nAnd a newline.',
]
ids = [
    'simple',
    'newline',
    'newlines',
    'breakchar',
    'breakchar_newline'
]

@pytest.fixture(params=strings, ids=ids)
def string(request):
    """String to perform TSL on."""
    return request.param

# @pytest.fixture()
# def options(request):
#     """Options for TSL."""
#     if hasattr(request, 'param'):
#         return request.param
#     return {}
