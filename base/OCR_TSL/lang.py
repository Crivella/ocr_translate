from .. import models as m

lang_src = m.Language.objects.get(name='ja')
lang_dst = m.Language.objects.get(name='en')