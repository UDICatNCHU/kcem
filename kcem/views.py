# -*- coding: utf-8 -*-
from django.http import JsonResponse
from djangoApiDec.djangoApiDec import queryString_required
from kcem import WikiKCEM
from udic_nlp_API.settings_database import uri

# Create your views here.
@queryString_required(['keyword'])
k = WikiKCEM(uri)
def kcem(request):
    """Generate list of term data source files
    Returns:
        if contains invalid queryString key, it will raise exception.
    """
    keyword = request.GET['keyword']
    return JsonResponse(k.findParent(keyword), safe=False)