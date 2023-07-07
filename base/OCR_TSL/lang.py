from .. import models as m

lang_src = m.Language.objects.get(name='ja')
lang_dst = m.Language.objects.get(name='en')

def get_lang_src():
    return lang_src

def get_lang_dst():
    return lang_dst

def load_lang_src(name):
    global lang_src
    lang_src = m.Language.objects.get(name=name)

def load_lang_dst(name):
    global lang_dst
    lang_dst = m.Language.objects.get(name=name)