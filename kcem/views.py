# -*- coding: utf-8 -*-
from django.http import JsonResponse
from djangoApiDec.djangoApiDec import queryString_required
from KCEM import KCEM
from udic_nlp_API.settings_database import uri
from django.shortcuts import render

# Create your views here.
@queryString_required(['lang', 'keyword', 'kcm', 'kem'])
def kcem(request):
    import json, requests
    """Generate list of term data source files
    Returns:
        if contains invalid queryString key, it will raise exception.
    """
    keyword = request.GET['keyword']
    lang = request.GET['lang']
    kcm = request.GET['kcm']
    kem = request.GET['kem']
    k = KCEM(uri)
    return JsonResponse(k.get(keyword, lang, num = int(request.GET['num']) if 'num' in request.GET else 10, kem_topn_num=kem, kcm_topn_num=kcm), safe=False)