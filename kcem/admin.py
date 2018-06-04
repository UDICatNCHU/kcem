from django.contrib import admin
from kcem.models import *

class HypernyAdmin(admin.ModelAdmin):
    search_fields = ['key']

admin.site.register(Hypernym, HypernyAdmin)

class CategoryAdmin(admin.ModelAdmin):
    search_fields = ['cat_title']

admin.site.register(Category, CategoryAdmin)

class CategorylinksAdmin(admin.ModelAdmin):
    search_fields = ['cl_to', 'cl_from']

admin.site.register(Categorylinks, CategorylinksAdmin)

class PageAdmin(admin.ModelAdmin):
    search_fields = ['page_id', 'page_title']

admin.site.register(Page, PageAdmin)

class PagelinksAdmin(admin.ModelAdmin):
    search_fields = ['page_id', 'page_title']

admin.site.register(Pagelinks, PagelinksAdmin)

class RedirectAdmin(admin.ModelAdmin):
    search_fields = ['page_id', 'page_title']

admin.site.register(Redirect, RedirectAdmin)