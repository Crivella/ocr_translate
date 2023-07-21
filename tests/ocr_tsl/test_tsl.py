"""Tests for translation module."""

import pytest

from ocr_translate.ocr_tsl import tsl

options = [
        {},
        {'break_newlines': False},
        {'break_chars': '?.!'},
        {'ignore_chars': '?.!'},
        {'break_newlines': False, 'break_chars': '?.!'},
        {'break_newlines': False, 'ignore_chars': '?.!'},
    ]

# @pytest.mark.parametrize(
#     'options',
#     [
#         {},
#         {'break_newlines': False},
#         {'break_chars': '?.!'},
#         {'ignore_chars': '?.!'},
#         {'break_newlines': False, 'break_chars': '?.!'},
#         {'break_newlines': False, 'ignore_chars': '?.!'},
#     ],
#     ids=[
#         'default',
#         'nosplitNL',
#         'split-breakchar',
#         'ignore-chars',
#         'split-breakchar_nosplitNL',
#         'ignore-chars_nosplitNL'
#     ]
# )
def test_pre_tokenize(string, data_regression):
    """Test tsl module."""
    res = []
    for option in options:
        dct = {
            'string': string,
            'options': option,
            'tokens': tsl.pre_tokenize(string, **option)
        }
        res.append(dct)

    data_regression.check({'res': res})

# def test_pipeline(text, monkeypatch):
#     def _mock_tokenizer(text, lang_src, lang_dst, options):
#         return tsl.pre_tokenize(text, **options)
#     def _mock_tsl_pipeline(text, lang_src, lang_dst, options):
#         return text
