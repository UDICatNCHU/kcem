# -*- coding: utf-8 -*-
from django.http import JsonResponse
from djangoApiDec.djangoApiDec import queryString_required
from kcem.apps import KCEM
from udic_nlp_API.settings_database import uri
import json

multilanguage_model = {
    'zh': KCEM('zh', uri)
}
# Create your views here.
@queryString_required(['keyword', 'lang'])
def kcem(request):
    """Generate list of term data source files
    Returns:
        if contains invalid queryString key, it will raise exception.
    """
    keyword = request.GET['keyword']
    lang = request.GET['lang']
    return JsonResponse(multilanguage_model[lang].get(keyword), safe=False)