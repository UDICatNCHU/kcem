# -*- coding: utf-8 -*-
from django.http import JsonResponse
from djangoApiDec.djangoApiDec import queryString_required
from kcem import WikiKCEM
from kem import KEM
from scipy import spatial
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
def kcemContext(request):
    if request.POST and 'docvec' in request.POST:
        docvec = json.loads(request.POST.dict()['docvec'])
        keyword = request.GET['keyword']

        # Because result would has a key 全部消歧義頁面
        # these are all ambiguous keyword
        # so need some post-processing
        # that's the reason why this api exists !
        bestChild, MaxSimilarity  = '', 0

        for child in k.child(keyword)['leafNode']:
            vec = kemObject.getVect(child)['value']
            similarity = 1 - spatial.distance.cosine(vec, docvec) if vec != [0] * 400 and docvec != [0]*400 else 0
            if similarity > MaxSimilarity and child != keyword:
                bestChild = child
                MaxSimilarity = similarity

        return JsonResponse(k.get(bestChild), safe=False)
    return JsonResponse({}, safe=False)

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
