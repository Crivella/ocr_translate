import re

from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, M2M100Tokenizer

from ..models import TSLModel
from .base import dev, root

tsl_model_id = "staka/fugumt-ja-en"

mid = root / 'translate' / tsl_model_id
tsl_model = AutoModelForSeq2SeqLM.from_pretrained(mid).to(dev)
tsl_tokenizer = AutoTokenizer.from_pretrained(mid)

# tsl_model = 1
tsl_model_obj, _ = TSLModel.objects.get_or_create(name=tsl_model_id)

special = re.compile("([・・.!。?]+)")
def tsl_pipeline(text, lang_src, lang_dst):
    tsl_tokenizer.src_lang = lang_src
                           
    res = []
    text = special.sub(r"\1\n", text)
    for tok in filter(None, text.split('\n')):
        # print(tok)
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
        # print(tsl)
        res.append(' '.join(tsl))

    return ' '.join(res)