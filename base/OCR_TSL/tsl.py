import logging
import re

from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, M2M100Tokenizer

from .. import models as m
from ..queues import tsl_queue as q
from .base import dev, load_hugginface_model

logger = logging.getLogger('ocr.general')

tsl_model_id = None
tsl_model = None
tsl_tokenizer = None
tsl_model_obj = None

def unload_tsl_model():
    global tsl_model_obj, tsl_model, tsl_tokenizer, tsl_model_id

    logger.info(f'Unloading TSL model: {tsl_model_id}')
    tsl_model = None
    tsl_tokenizer = None
    tsl_model_obj = None
    tsl_model_id = None

    if dev == 'cuda':
        import torch
        torch.cuda.empty_cache()

def load_tsl_model(model_id):
    global tsl_model_obj, tsl_model, tsl_tokenizer, tsl_model_id

    if tsl_model_id == model_id:
        return

    logger.info(f'Loading TSL model: {model_id}')
    res = load_hugginface_model(model_id, request=['seq2seq', 'tokenizer'])
    tsl_model = res['seq2seq']
    tsl_tokenizer = res['tokenizer']

    tsl_model_obj, _ = m.TSLModel.objects.get_or_create(name=model_id)
    tsl_model_id = model_id

def get_tsl_model() -> m.TSLModel:
    return tsl_model_obj

special = re.compile("([・・.!。?♥♡♪〜]+)")
def _tsl_pipeline(text: str, lang_src: str, lang_dst: str, options: dict = {}):
    tsl_tokenizer.src_lang = lang_src

    break_newlines = options.get('break_newlines', True)
    break_chars = options.get('break_chars', None)
    ignore_chars = options.get('ignore_chars', None)

    min_max_new_tokens = options.get('min_max_new_tokens', 10)
    max_max_new_tokens = options.get('min_max_new_tokens', 512)
    max_new_tokens = options.get('max_new_tokens', 10)
    max_new_tokens_ratio = options.get('max_new_tokens_ratio', 1)
                           
    if break_chars is not None:
        text = re.sub(f'[{break_chars}]', '\n', text)
    if ignore_chars is not None:
        text = re.sub(f'[{ignore_chars}]', '', text)
    text = re.sub(r'\n+', '\n', text)
    if break_newlines:
        tokens = text.split('\n')
    else:
        tokens = [text] 
   
    res = []
    for tok in filter(None, tokens):
        logger.debug(f'TSL: {tok}')
        encoded = tsl_tokenizer(tok, return_tensors="pt")
        ntok = encoded['input_ids'].flatten().size()[0]
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
            "max_new_tokens": mnt,
        }
        if isinstance(tsl_tokenizer, M2M100Tokenizer):
            kwargs["forced_bos_token_id"] = tsl_tokenizer.get_lang_id(lang_dst)

        generated_tokens = tsl_model.generate(
            **encoded,
            **kwargs,
            )
        tsl = tsl_tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)
        logger.debug(f'TSL: {tsl}')
        res.append(' '.join(tsl))

    return ' '.join(res)

def tsl_pipeline(*args, id, **kwargs):
    msg = q.put(
        id = id,
        msg = {'args': args, 'kwargs': kwargs},
        handler = _tsl_pipeline,
    )

    return msg.response()

def tsl_run(text_obj: m.Text, src: m.Language, dst: m.Language, options: m.OptionDict = None, force: bool = False) -> m.Text:
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
        logger.info('Running TSL')
        id = (text_obj.id, model_obj.id)
        opt_dct = options_obj.options
        opt_dct.setdefault('break_chars', src.break_chars)
        opt_dct.setdefault('ignore_chars', src.ignore_chars)
        new = tsl_pipeline(
            text_obj.text,
            getattr(src, model_obj.language_format),
            getattr(dst, model_obj.language_format),
            id=id, 
            options=opt_dct
            )
        text_obj, _ = m.Text.objects.get_or_create(
            text = new,
            )
        params['result'] = text_obj
        tsl_run_obj = m.TranslationRun.objects.create(**params)
    else:
        logger.info('Reusing TSL')
        # new = tsl_run_obj.result.text

    return tsl_run_obj.result
