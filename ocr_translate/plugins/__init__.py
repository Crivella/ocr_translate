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
"""Entrypoints for creating models."""


easyocr_box_model_data = {
    # Name of the model
    'name': 'easyocr',
    # List of ISO-639-1 codes supported by the model
    'lang': ['en', 'ja', 'zh', 'ko'],
    # How the model requires the codes to be passed (one of 'iso1', 'iso2b', 'iso2t', 'iso3')
    # If the models codes only partially match or are totally different from one of the ISO standards, see iso1_map
    'lang_code': 'iso1',
    # Name of the entrypoint for the model (should match what is used in pyproject.toml)
    'entrypoint': 'easyocr.box',
    # Maps ISO-639-1 codes to the codes used by the model. Does not need to map every language, only those that are
    # different from getattr(lang: m.Language, lang_code)
    'iso1_map': {
        'ce': 'che',
        'zh': 'ch_sim',
        'zht': 'ch_tra',
        'tg': 'tjk',
    }
}

tesseract_ocr_model_data = {
    'name': 'tesseract',
    'lang': [
        'af', 'sq', 'am', 'ar', 'hy', 'as', 'az', 'eu', 'be', 'bn', 'bs', 'br', 'bg', 'my', 'zh', 'zht', 'co', 'hr',
        'cs', 'da', 'dz', 'en', 'eo', 'et', 'fo', 'fi', 'fr', 'fy', 'gl', 'ka', 'de', 'gu', 'he', 'hi', 'hu', 'is',
        'id', 'iu', 'ga', 'it', 'ja', 'jv', 'kn', 'kk', 'km', 'ko', 'lo', 'la', 'lv', 'lt', 'mk', 'ms', 'ml', 'mt',
        'mi', 'mr', 'mn', 'ne', 'no', 'or', 'fa', 'pl', 'pt', 'qu', 'ru', 'sa', 'sr', 'sd', 'sk', 'sl', 'su', 'sw',
        'sv', 'tg', 'ta', 'tt', 'te', 'th', 'bo', 'ti', 'tr', 'uk', 'ur', 'uz', 'vi', 'cy', 'yi', 'yo'
        ],
    'lang_code': 'iso3',
    'entrypoint': 'tesseract.ocr',
    'iso1_map': {
        'et': 'est',
        'iu': 'iku',
        'lv': 'lav',
        'ms': 'msa',
        'mn': 'mon',
        'ne': 'nep',
        'no': 'nor',
        'or': 'ori',
        'fa': 'fas',
        'qu': 'que',
        'sw': 'swa',
        'uz': 'uzb',
        'yi': 'yid',
    }
}

khawhite_ocr_model_data = {
    'name': 'kha-white/manga-ocr-base',
    'lang': ['ja'],
    'lang_code': 'iso1',
    'entrypoint': 'hugginface.ved'
}

helsinki_zh_en_tsl_model_data = {
    'name': 'Helsinki-NLP/opus-mt-zh-en',
    'lang_src': ['zh'],
    'lang_dst': ['en'],
    'lang_code': 'iso1',
    'default_options': {
        'break_newlines': False
    },
    'entrypoint': 'hugginface.seq2seq'
}

helsinki_ja_en_tsl_model_data = {
    'name': 'Helsinki-NLP/opus-mt-ja-en',
    'lang_src': ['ja'],
    'lang_dst': ['en'],
    'lang_code': 'iso1',
    'default_options': {
        'break_newlines': True
    },
    'entrypoint': 'hugginface.seq2seq'
}

helsinki_ko_en_tsl_model_data = {
    'name': 'Helsinki-NLP/opus-mt-ko-en',
    'lang_src': ['ko'],
    'lang_dst': ['en'],
    'lang_code': 'iso1',
    'default_options': {
        'break_newlines': False
    },
    'entrypoint': 'hugginface.seq2seq'
}

helsinki_zh_en_tsl_model_data = {
    'name': 'Helsinki-NLP/opus-mt-zh-en',
    'lang_src': ['zh'],
    'lang_dst': ['en'],
    'lang_code': 'iso1',
    'default_options': {
        'break_newlines': False
    },
    'entrypoint': 'hugginface.seq2seq'
}

staka_fugumt_ja_en_tsl_model_data = {
    'name': 'staka/fugumt-ja-en',
    'lang_src': ['ja'],
    'lang_dst': ['en'],
    'lang_code': 'iso1',
    'default_options': {
        'break_newlines': True
    },
    'entrypoint': 'hugginface.seq2seq'
}

facebook_m2m100_418m_tsl_model_data = {
    'name': 'facebook/m2m100_418M',
    'lang_src': [
        'af', 'am', 'ar', 'az', 'ba', 'be', 'bg', 'bn', 'br', 'bs', 'cs', 'cy', 'da', 'de', 'en', 'et', 'fa','ff',
        'fi', 'fr', 'fy', 'ga', 'gl', 'gu', 'ha', 'he', 'hi', 'hr', 'hu', 'hy', 'id', 'ig', 'is', 'it', 'ja', 'jv',
        'ka', 'kk', 'km', 'kn', 'ko', 'lg', 'ln', 'lo', 'lt', 'lv', 'mg', 'mk', 'ml', 'mn', 'mr', 'ms', 'my', 'ne',
        'no', 'oc', 'or', 'pl', 'pt', 'ru', 'sd', 'sk', 'sl', 'so', 'sq', 'sr', 'ss', 'su', 'sv', 'sw', 'ta', 'th',
        'tl', 'tn', 'tr', 'uk', 'ur', 'uz', 'vi', 'wo', 'xh', 'yi', 'yo', 'zh', 'zht', 'zu'
        ],
    'lang_dst': [
        'af', 'am', 'ar', 'az', 'ba', 'be', 'bg', 'bn', 'br', 'bs', 'cs', 'cy', 'da', 'de', 'en', 'et', 'fa','ff',
        'fi', 'fr', 'fy', 'ga', 'gl', 'gu', 'ha', 'he', 'hi', 'hr', 'hu', 'hy', 'id', 'ig', 'is', 'it', 'ja', 'jv',
        'ka', 'kk', 'km', 'kn', 'ko', 'lg', 'ln', 'lo', 'lt', 'lv', 'mg', 'mk', 'ml', 'mn', 'mr', 'ms', 'my', 'ne',
        'no', 'oc', 'or', 'pl', 'pt', 'ru', 'sd', 'sk', 'sl', 'so', 'sq', 'sr', 'ss', 'su', 'sv', 'sw', 'ta', 'th',
        'tl', 'tn', 'tr', 'uk', 'ur', 'uz', 'vi', 'wo', 'xh', 'yi', 'yo', 'zh', 'zht', 'zu'
        ],
    'lang_code': 'iso1',
    'default_options': {
        'break_newlines': False
    },
    'entrypoint': 'hugginface.seq2seq',
    'iso1_map': {
        'zht': 'zh'
    }
}

facebook_m2m100_1_2b_tsl_model_data = {
    'name': 'facebook/m2m100_1.2B',
    'lang_src': [
        'af', 'am', 'ar', 'az', 'ba', 'be', 'bg', 'bn', 'br', 'bs', 'cs', 'cy', 'da', 'de', 'en', 'et', 'fa','ff',
        'fi', 'fr', 'fy', 'ga', 'gl', 'gu', 'ha', 'he', 'hi', 'hr', 'hu', 'hy', 'id', 'ig', 'is', 'it', 'ja', 'jv',
        'ka', 'kk', 'km', 'kn', 'ko', 'lg', 'ln', 'lo', 'lt', 'lv', 'mg', 'mk', 'ml', 'mn', 'mr', 'ms', 'my', 'ne',
        'no', 'oc', 'or', 'pl', 'pt', 'ru', 'sd', 'sk', 'sl', 'so', 'sq', 'sr', 'ss', 'su', 'sv', 'sw', 'ta', 'th',
        'tl', 'tn', 'tr', 'uk', 'ur', 'uz', 'vi', 'wo', 'xh', 'yi', 'yo', 'zh', 'zht', 'zu'
        ],
    'lang_dst': [
        'af', 'am', 'ar', 'az', 'ba', 'be', 'bg', 'bn', 'br', 'bs', 'cs', 'cy', 'da', 'de', 'en', 'et', 'fa','ff',
        'fi', 'fr', 'fy', 'ga', 'gl', 'gu', 'ha', 'he', 'hi', 'hr', 'hu', 'hy', 'id', 'ig', 'is', 'it', 'ja', 'jv',
        'ka', 'kk', 'km', 'kn', 'ko', 'lg', 'ln', 'lo', 'lt', 'lv', 'mg', 'mk', 'ml', 'mn', 'mr', 'ms', 'my', 'ne',
        'no', 'oc', 'or', 'pl', 'pt', 'ru', 'sd', 'sk', 'sl', 'so', 'sq', 'sr', 'ss', 'su', 'sv', 'sw', 'ta', 'th',
        'tl', 'tn', 'tr', 'uk', 'ur', 'uz', 'vi', 'wo', 'xh', 'yi', 'yo', 'zh', 'zht', 'zu'
        ],
    'lang_code': 'iso1',
    'default_options': {
        'break_newlines': False
    },
    'entrypoint': 'hugginface.seq2seq',
    'iso1_map': {
        'zht': 'zh'
    }
}
