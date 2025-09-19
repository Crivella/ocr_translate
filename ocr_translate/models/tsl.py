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
from typing import Generator, Union

from django.db import models

from .. import queues
from ..messaging import Message
from .base import BaseModel, Language, OptionDict, Text, safe_get_or_create

logger = logging.getLogger('ocr.general')

class TSLModel(BaseModel):
    """Translation models using hugging space naming convention"""
    ALLOWED_OPTIONS = {
        'ignore_chars': {
            'type': str,
            'default': ('cascade', ['lang_src', 'tsl_model'], ''),
            'description': 'Characters to ignore during translation.',
        },
        'break_chars': {
            'type': str,
            'default': ('cascade', ['lang_src', 'tsl_model'], ''),
            'description': (
                'Characters on which lines will be split for translation.\n'
                'The split lines are translated separately (no context between them) and then merged back together.)'
                ),
        },
        'allowed_start_end': {
            'type': str,
            'default': ('cascade', ['lang_src', 'tsl_model'], ''),
            'description': (
                'Characters allowed at the start and end of a line.\n'
                'Some models like tesseract, will detect the edges of text bubbles as text and spit out garbage '
                'at the start/end of the translated line. This option will filter out any caracter that is not '
                'allowed at the start/end of a line.'
                ),
        },
        'break_newlines': {
            'type': bool,
            'default': ('cascade', ['lang_src', 'tsl_model'], False),
            'description': 'Split lines on newlines. If false the newlines will be replaced with spaces.',
        },
        'restore_missing_spaces': {
            'type': bool,
            'default': ('cascade', ['lang_src', 'tsl_model'], False),
            'description': (
                'Some models will OCR text without spaces between some of the words.\n'
                'This option will attempt to restore the missing spaces by finding the shortest valid decomposition '
                'also keeping into account the word frequency.\n'
                '(Only available if a trie is loaded for the source language.)'
                ),
        },
        'restore_dash_newlines': {
            'type': bool,
            'default': ('cascade', ['lang_src', 'tsl_model'], False),
            'description': (
                'Text can be written with dash splitting a word onto a new line.\n'
                'If this option is enabled, dashes preceded by a character and followed by a newline will be removed '
                'togheter with the newline to merge the word back together.'
                ),
        },
    }
    CREATE_LANG_KEYS = {'lang_src': 'src_languages', 'lang_dst': 'dst_languages'}

    entrypoint_namespace = 'ocr_translate.tsl_models'

    src_languages = models.ManyToManyField(Language, related_name='tsl_models_src')
    dst_languages = models.ManyToManyField(Language, related_name='tsl_models_dst')

    @staticmethod
    def pre_tokenize( # pylint: disable=too-many-branches
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
            allowed_start_end (str, optional): String of characters allowed at the start and end of a line.
            break_newlines (bool, optional): Whether to break on newlines. Defaults to True.
            restore_missing_spaces (bool, optional): Whether to restore missing spaces (2 word with no space between).
            restore_dash_newlines (bool, optional): Whether to restore dash-newlines (word broken with a -newline).
                Defaults to False.

        Returns:
            list[str]: List of string tokens.
        """
        if isinstance(break_newlines, str):
            break_newlines = break_newlines.lower() == 'true'
        if isinstance(restore_missing_spaces, str):
            restore_missing_spaces = restore_missing_spaces.lower() == 'true'
        if isinstance(restore_dash_newlines, str):
            restore_dash_newlines = restore_dash_newlines.lower() == 'true'
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
        if ignore_chars:
            text = re.sub(f'[{ignore_chars}]+', '', text)
        if break_chars is None:
            break_chars = ''
        if break_newlines:
            break_chars += '\n'
        else:
            text = text.replace('\n', ' ')

        trie = Language.get_loaded_trie()
        if restore_missing_spaces and not trie is None:
            res = []
            for split in text.lower().split(' '):
                if not trie.search(split, strict=False):
                    decomposed = trie.decompose(split, min_length=1)
                    if decomposed:
                        res.append(decomposed)
                    else:
                        res.append([[split]])
                else:
                    res.append([[split]])

            # Use a list of word frequencies to determine the best split
            def sum_freq(lst: list) -> float:
                return sum(trie.get_freq(w) for w in lst) / len(lst)**4.0

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


    def _translate(
            self,
            tokens: list, src_lang: str, dst_lang: str, options: dict = None) -> str | list[str]:
        """PLACEHOLDER (to be implemented via entrypoint): Translate a text using a the loaded model.

        Args:
            tokens (list): list or list[list] of string tokens to be translated.
            lang_src (str): Source language.
            lang_dst (str): Destination language.
            options (dict, optional): Options for the translation. Defaults to {}.

        Raises:
            TypeError: If text is not a string or a list of strings.

        Returns:
            Union[str,list[str]]: Translated text. If text is a list, returns a list of translated strings.
        """
        # Redefine this method with the same signature as above
        # Should return a string with the translated text.
        # IMPORTANT: the main codebase treats this function as batchable:
        # The input `tokens` can be a list of strings or a list of list of strings. The output should match the input
        #   being a string or list of strings.
        # (This is used to leverage the capability of pytorch to batch inputs and outputs for faster performances,
        #   or it can also used to write a plugin for an online service by using a single request for multiple inputs
        #   using some separator that the service will leave unaltered.)
        raise NotImplementedError('The base model class does not implement this method.')

    def find_manual(self,  text_obj: 'Text', src: 'Language', dst: 'Language') -> 'TranslationRun':
        """Find a manual translation run for the given text with the specified source and destination languages.
        Args:
            text_obj (m.Text): Text object from the database to translate.
            src (m.Language): Source language object from the database.
            dst (m.Language): Destination language object from the database.

        Returns:
            m.TranslationRun: The TranslationRun object from the database.
        """
        manual_model, _ = TSLModel.objects.get_or_create(name='manual')
        params = {
            'model': manual_model,
            'lang_src': src,
            'lang_dst': dst,
            'text': text_obj,
            'options': OptionDict.objects.get(options={})
        }
        # logger.debug(f'Looking for manual TSL with params: {params}')
        return TranslationRun.objects.filter(**params).first()


    def translate(
            self,
            text_obj: 'Text', src: 'Language', dst: 'Language', options: 'OptionDict' = None,
            force: bool = False,
            block: bool = True,
            favor_manual: bool = True,
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
            favor_manual (bool, optional): Whether to favor manual translations over TSL. Defaults to True.
            lazy (bool, optional): Whether to raise an error if the TSL run is not found. Defaults to False.

        Raises:
            ValueError: If lazy and force are both True or if lazy is True and the TSL run is not found.

        Yields:
            Generator[Union[Message, m.Text], None, None]:
                If block is False, yields a Message object for the TSL run first and the resulting Text object second.
                If block is True, yields the resulting Text object.
        """
        if lazy and force:
            raise ValueError('Cannot force + lazy TSL run')
        # Check if a ManualModel is being used
        tsl_run_obj = None
        if favor_manual:
            tsl_run_obj = self.find_manual(text_obj, src, dst)
        if tsl_run_obj is None:
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
            id_ = (text_obj.id, self.id, options_obj.id, src.id, dst.id, options_obj.id)
            batch_id = (self.id, options_obj.id, src.id, dst.id, options_obj.id)
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
            text_obj = safe_get_or_create(Text, text=new)
            params['result'] = text_obj
            tsl_run_obj = TranslationRun.objects.create(**params)
        else:
            if not block:
                # Both branches should have the same number of yields
                yield None
            manual = ''
            if tsl_run_obj.model.name == 'manual':
                manual = 'manual '
            logger.info(f'Reusing {manual}TSL <{tsl_run_obj.id}>')

        yield tsl_run_obj.result

class TranslationRun(models.Model):
    """Translation run on a text using a specific model"""
    options = models.ForeignKey(OptionDict, on_delete=models.CASCADE, related_name='trans_options')

    lang_src = models.ForeignKey(Language, on_delete=models.CASCADE, related_name='trans_src')
    lang_dst = models.ForeignKey(Language, on_delete=models.CASCADE, related_name='trans_dst')

    text = models.ForeignKey(Text, on_delete=models.CASCADE, related_name='to_trans')
    model = models.ForeignKey(TSLModel, on_delete=models.CASCADE, related_name='tsl_runs')
    result = models.ForeignKey(Text, on_delete=models.CASCADE, related_name='from_trans')
