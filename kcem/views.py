# -*- coding: utf-8 -*-
from django.http import JsonResponse
from djangoApiDec.djangoApiDec import queryString_required
from kcem import WikiKCEM
from kem import KEM
from scipy import spatial
from udic_nlp_API.settings_database import uri
import json

k = WikiKCEM(uri)
kemObject = KEM(uri)
# Create your views here.
@queryString_required(['keyword'])
def kcem(request):
    """Generate list of term data source files
    Returns:
        if contains invalid queryString key, it will raise exception.
    """
    keyword = request.GET['keyword']
    if request.POST and 'docvec' in request.POST:
        docvec = json.loads(request.POST.dict()['docvec'])

        # Because result would has a key 全部消歧義頁面
        # these are all ambiguous keyword
        # so need some post-processing
        # that's the reason why this api exists !
        bestChild, MaxSimilarity  = '', 0

        for child in k.child(keyword)['leafNode']:
            vec = kemObject.getVect(child)['value']
            similarity = 1 - spatial.distance.cosine(vec, docvec) if vec != [0] * 400 and docvec != [0]*400 else -1
            if similarity > MaxSimilarity and child != keyword:
                bestChild = child
                MaxSimilarity = similarity

        return JsonResponse(k.get(bestChild), safe=False)
    return JsonResponse(k.get(keyword), safe=False)

def child(request):
    keyword = request.GET['keyword']
    return JsonResponse(k.child(keyword), safe=False)

def counterKCEM(request):
    if request.POST and 'counter' in request.POST:
        counter = json.loads(request.POST.dict()['counter'])
        EntityOnly = True if 'EntityOnly' in request.GET else False
        try:
            return JsonResponse(k.counterKCEM(counter, EntityOnly), safe=False)
        except Exception as e:
            print(e)
            return JsonResponse([], safe=False)
    return JsonResponse([], safe=False)
