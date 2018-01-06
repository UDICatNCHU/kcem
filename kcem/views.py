# -*- coding: utf-8 -*-
from django.http import JsonResponse
from djangoApiDec.djangoApiDec import queryString_required
from kcem import WikiKCEM
from udic_nlp_API.settings_database import uri
import json

k = WikiKCEM(uri)
# Create your views here.
@queryString_required(['keyword'])
def kcem(request):
    """Generate list of term data source files
    Returns:
        if contains invalid queryString key, it will raise exception.
    """
    keyword = request.GET['keyword']
    return JsonResponse(k.get(keyword), safe=False)

@queryString_required(['keyword'])
def child(request):
    keyword = request.GET['keyword']
    return JsonResponse(k.child(keyword), safe=False)

def topn(request):
    if request.POST and 'doc' in request.POST:
        doc = request.POST.dict()['doc']
        num = int(request.GET['num']) if 'num' in request.GET else None
        try:
            return JsonResponse(k.topn(doc, num), safe=False)
        except Exception as e:
            print(e)
            return JsonResponse([], safe=False)
    return JsonResponse([], safe=False)

def countertopn(request):
    if request.POST and 'doc' in request.POST:
        doc = json.loads(request.POST.dict()['doc'])
        num = int(request.GET['num']) if 'num' in request.GET else None
        EntityOnly = True if 'EntityOnly' in request.GET else False
        try:
            return JsonResponse(k.countertopn(doc, num, EntityOnly), safe=False)
        except Exception as e:
            print(e)
            return JsonResponse([], safe=False)
    return JsonResponse([], safe=False)