# -*- coding: utf-8 -*-
from django.http import JsonResponse
from djangoApiDec.djangoApiDec import queryString_required
from kcem import KCEM
from udic_nlp_API.settings_database import uri
from django.shortcuts import render

# Create your views here.
@queryString_required(['keyword'])
def kcem(request):
    import json, requests
    """Generate list of term data source files
    Returns:
        if contains invalid queryString key, it will raise exception.
    """
    keyword = request.GET['keyword']
    k = KCEM(uri)
    return JsonResponse(k.get(keyword, num = int(request.GET['num']) if 'num' in request.GET else 10), safe=False)