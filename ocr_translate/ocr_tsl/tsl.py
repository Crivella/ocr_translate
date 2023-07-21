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
"""Functions and piplines to perform translation on text."""
import logging
import re
from typing import Generator, Hashable, Union

import torch
from transformers import M2M100Tokenizer

from .. import models as m
from ..messaging import Message
from ..queues import tsl_queue as q
from .base import dev, load_hugginface_model

logger = logging.getLogger('ocr.general')

TSL_MODEL_ID = None
TSL_MODEL = None
TSL_TOKENIZER = None
TSL_MODEL_OBJ = None

def unload_tsl_model():
    """Remove the current TSL model from memory."""
    global TSL_MODEL_OBJ, TSL_MODEL, TSL_TOKENIZER, TSL_MODEL_ID

    logger.info(f'Unloading TSL model: {TSL_MODEL_ID}')
    TSL_MODEL = None
    TSL_TOKENIZER = None
    TSL_MODEL_OBJ = None
    TSL_MODEL_ID = None

    if dev == 'cuda':
        torch.cuda.empty_cache()

def load_tsl_model(model_id):
    """Load a TSL model into memory."""
    global TSL_MODEL_OBJ, TSL_MODEL, TSL_TOKENIZER, TSL_MODEL_ID

    if TSL_MODEL_ID == model_id:
        return

    logger.info(f'Loading TSL model: {model_id}')
    res = load_hugginface_model(model_id, request=['seq2seq', 'tokenizer'])
    TSL_MODEL = res['seq2seq']
    TSL_TOKENIZER = res['tokenizer']

    TSL_MODEL_OBJ, _ = m.TSLModel.objects.get_or_create(name=model_id)
    TSL_MODEL_ID = model_id

def get_tsl_model() -> m.TSLModel:
    """Get the current TSL model."""
    return TSL_MODEL_OBJ

def pre_tokenize(
        text: str,
        ignore_chars: str = None, break_chars: str = None, break_newlines: bool = True
        ) -> list[str]:
    """Pre-tokenize a text string.

    Args:
        text (str): Text to tokenize.
        ignore_chars (str, optional): String of characters to ignore. Defaults to None.
        break_chars (str, optional): String of characters to break on. Defaults to None.
        break_newlines (bool, optional): Whether to break on newlines. Defaults to True.

    Returns:
        list[str]: List of string tokens.
    """
    if ignore_chars is not None:
        text = re.sub(f'[{ignore_chars}]+', '', text)
    if break_chars is None:
        break_chars = ''
    if break_newlines:
        break_chars += '\n'

    break_chars = re.escape(break_chars)
    tokens = text
    if len(break_chars) > 0:
        tokens = re.split(f'[{break_chars}+]', text)

    if isinstance(tokens, str):
        tokens = [text]
    return list(filter(None, tokens))

def _tsl_pipeline(
        text: Union[str,list[str]],
        lang_src: str, lang_dst: str,
        options: dict = None
        ) -> Union[str,list[str]]:
    """Translate a text using a TSL model.

    Args:
        text (Union[str,list[str]]): Text to translate. Can be batched to a list of strings.
        lang_src (str): Source language.
        lang_dst (str): Destination language.
        options (dict, optional): Options for the translation. Defaults to {}.

    Raises:
        TypeError: If text is not a string or a list of strings.

    Returns:
        Union[str,list[str]]: Translated text. If text is a list, returns a list of translated strings.
    """
    if options is None:
        options = {}
    TSL_TOKENIZER.src_lang = lang_src

    break_newlines = options.get('break_newlines', True)
    break_chars = options.get('break_chars', None)
    ignore_chars = options.get('ignore_chars', None)

    min_max_new_tokens = options.get('min_max_new_tokens', 20)
    max_max_new_tokens = options.get('max_max_new_tokens', 512)
    max_new_tokens = options.get('max_new_tokens', 20)
    max_new_tokens_ratio = options.get('max_new_tokens_ratio', 3)

    args = (ignore_chars, break_chars, break_newlines)
    if isinstance(text, list):
        tokens = [pre_tokenize(t, *args) for t in text]
    elif isinstance(text, str):
        tokens = pre_tokenize(text, *args)
    else:
        raise TypeError(f'Unsupported type for text: {type(text)}')

    logger.debug(f'TSL: {tokens}')
    if len(tokens) == 0:
        return ''
    encoded = TSL_TOKENIZER(
        tokens,
        return_tensors='pt',
        padding=True,
        truncation=True,
        is_split_into_words=True
        )
    ntok = encoded['input_ids'].shape[1]
    encoded.to(dev)

    mnt = min(
        max_max_new_tokens,
        max(
            min_max_new_tokens,
            max_new_tokens,
            max_new_tokens_ratio * ntok
        )
    )

    kwargs = {
        'max_new_tokens': mnt,
    }
    if isinstance(TSL_TOKENIZER, M2M100Tokenizer):
        kwargs['forced_bos_token_id'] = TSL_TOKENIZER.get_lang_id(lang_dst)

    logger.debug(f'TSL ENCODED: {encoded}')
    logger.debug(f'TSL KWARGS: {kwargs}')
    generated_tokens = TSL_MODEL.generate(
        **encoded,
        **kwargs,
        )

    tsl = TSL_TOKENIZER.batch_decode(generated_tokens, skip_special_tokens=True)
    logger.debug(f'TSL: {tsl}')

    if isinstance(text, str):
        tsl = tsl[0]
    return tsl

def tsl_pipeline(*args, id_: Hashable, batch_id: Hashable = None, block: bool = True, **kwargs):
    """Queue a text translation pipeline.

    Args:
        id_ (Hashable): A unique identifier for the OCR task.
        block (bool, optional): Whether to block until the task is complete. Defaults to True.

    Returns:
        Union[str, Message]: The text extracted from the image (block=True) or a Message object (block=False).
    """
    msg = q.put(
        id_ = id_,
        batch_id = batch_id,
        msg = {'args': args, 'kwargs': kwargs},
        handler = _tsl_pipeline,
    )

    if block:
        return msg.response()
    return msg

def tsl_run(
        text_obj: m.Text, src: m.Language, dst: m.Language, options: m.OptionDict = None,
        force: bool = False,
        block: bool = True,
        lazy: bool = False
        ) -> Generator[Union[Message, m.Text], None, None]:
    """Run a TSL pipeline on a text object.

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
    model_obj = get_tsl_model()
    options_obj = options or m.OptionDict.objects.get(options={})
    params = {
        'options': options_obj,
        'text': text_obj,
        'model': model_obj,
        'lang_src': src,
        'lang_dst': dst,
    }
    tsl_run_obj = m.TranslationRun.objects.filter(**params).first()
    if tsl_run_obj is None or force:
        if lazy:
            raise ValueError('Value not found for lazy TSL run')
        logger.info('Running TSL')
        id_ = (text_obj.id, model_obj.id, options_obj.id, src.id, dst.id)
        batch_id = (model_obj.id, options_obj.id, src.id, dst.id)
        opt_dct = options_obj.options
        opt_dct.setdefault('break_chars', src.break_chars)
        opt_dct.setdefault('ignore_chars', src.ignore_chars)
        new = tsl_pipeline(
            text_obj.text,
            getattr(src, model_obj.language_format),
            getattr(dst, model_obj.language_format),
            options=opt_dct,
            id_=id_,
            batch_id=batch_id,
            block=block,
            )
        if not block:
            yield new
            new = new.response()
        text_obj, _ = m.Text.objects.get_or_create(
            text = new,
            )
        params['result'] = text_obj
        tsl_run_obj = m.TranslationRun.objects.create(**params)
    else:
        if not block:
            # Both branches should have the same number of yields
            yield None
        logger.info(f'Reusing TSL <{tsl_run_obj.id}>')
        # new = tsl_run_obj.result.text

    yield tsl_run_obj.result
