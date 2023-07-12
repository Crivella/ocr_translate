import logging
import re

from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, M2M100Tokenizer

from .. import models as m
from ..queues import tsl_queue as q
from .base import dev, load_model

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
    res = load_model(model_id, request=['seq2seq', 'tokenizer'])
    tsl_model = res['seq2seq']
    tsl_tokenizer = res['tokenizer']

    tsl_model_obj, _ = m.TSLModel.objects.get_or_create(name=model_id)
    tsl_model_id = model_id

def get_tsl_model() -> m.TSLModel:
    return tsl_model_obj

special = re.compile("([・・.!。?♥♡♪〜]+)")
def _tsl_pipeline(text: str, lang_src: str = 'ja', lang_dst: str = 'en'):
    tsl_tokenizer.src_lang = lang_src
                           
    res = []
    text = special.sub(r"\1\n", text)
    for tok in filter(None, text.split('\n')):
        logger.debug(f'TSL: {tok}')
        encoded = tsl_tokenizer(tok, return_tensors="pt")
        encoded.to(dev)

        kwargs = {}
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

def tsl_run(text_obj: m.Text, src: m.Language, dst: m.Language, options: dict = {}, force: bool = False) -> m.Text:
    global tsl_model_obj
    params = {
        'options': options,
        'text': text_obj,
        'model': tsl_model_obj,
        'lang_src': src,
        'lang_dst': dst,
    }
    tsl_run_obj = m.TranslationRun.objects.filter(**params).first()
    if tsl_run_obj is None or force:
        logger.info('Running TSL')
        id = (text_obj.id, tsl_model_obj.id)
        new = tsl_pipeline(text_obj.text, id=id)
        text_obj, _ = m.Text.objects.get_or_create(
            text = new,
            )
        params['result'] = text_obj
        tsl_run_obj = m.TranslationRun.objects.create(**params)
    else:
        logger.info('Reusing TSL')
        # new = tsl_run_obj.result.text

    return tsl_run_obj.result
