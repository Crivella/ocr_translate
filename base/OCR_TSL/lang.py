from .. import models as m

get_lang_src = None
get_lang_dst = None
# lang_src = m.Language.objects.get(name='ja')
# lang_dst = m.Language.objects.get(name='en')

def get_lang_src():
    return get_lang_src

def get_lang_dst():
    return get_lang_dst

def load_lang_src(iso1):
    global get_lang_src
    get_lang_src = m.Language.objects.get(iso1=iso1)

def load_lang_dst(iso1):
    global get_lang_dst
    get_lang_dst = m.Language.objects.get(iso1=iso1)