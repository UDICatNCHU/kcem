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
    if request.POST and 'docvec' in request.POST:
        return JsonResponse(k.get(keyword, request.POST['docvec']), safe=False)
    return JsonResponse(k.get(keyword), safe=False)

@queryString_required(['keywords'])
def kcemList(request):
    '''
    keywords: type array
    '''
    keywords = request.GET['keywords'].split()
    if request.POST and 'docvec' in request.POST:
        return JsonResponse(k.getList(keywords, request.POST['docvec']), safe=False)
    return JsonResponse(k.getList(keywords), safe=False)    

def child(request):
    keyword = request.GET['keyword']
    return JsonResponse(k.child(keyword), safe=False)