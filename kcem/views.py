# -*- coding: utf-8 -*-
from django.http import JsonResponse
from djangoApiDec.djangoApiDec import queryString_required
from kcem import WikiKCEM
from udic_nlp_API.settings_database import uri

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

def topn(request):
    if request.POST and 'doc' in request.POST:
        doc = request.POST.dict()['doc']
        num = request.GET['num'] if request.GET['num'] else -1
        try:
            return JsonResponse(k.topn(doc, num), safe=False)
        except Exception as e:
            print(e)
            return JsonResponse([], safe=False)
    return JsonResponse([], safe=False)