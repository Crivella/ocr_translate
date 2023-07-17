from .. import models as m

lang_src = None
lang_dst = None
# lang_src = m.Language.objects.get(name='ja')
# lang_dst = m.Language.objects.get(name='en')

def get_lang_src():
    return lang_src

def get_lang_dst():
    return lang_dst

def load_lang_src(iso1):
    global lang_src
    lang_src = m.Language.objects.get(iso1=iso1)

def load_lang_dst(iso1):
    global lang_dst
    lang_dst = m.Language.objects.get(iso1=iso1)