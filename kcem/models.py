# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from __future__ import unicode_literals

from django.db import models

class Hypernym(models.Model):
    key = models.CharField(db_index=True, max_length=255)
    value = models.TextField()

    def __str__(self):
        return self.key

class Category(models.Model):
    cat_id = models.AutoField(primary_key=True)
    cat_title = models.CharField(unique=True, max_length=255)
    cat_pages = models.IntegerField()
    cat_subcats = models.IntegerField()
    cat_files = models.IntegerField()
    
    class Meta:
        managed = False
        db_table = 'category'


class Categorylinks(models.Model):
    cl_from = models.IntegerField()
    cl_to = models.CharField(max_length=255)
    cl_sortkey = models.CharField(max_length=230)
    cl_timestamp = models.DateTimeField()
    cl_sortkey_prefix = models.CharField(max_length=255)
    cl_collation = models.CharField(max_length=32)
    cl_type = models.CharField(max_length=6)
    
    class Meta:
        managed = False
        db_table = 'categorylinks'
        unique_together = (('cl_from', 'cl_to'),)


class Page(models.Model):
    page_id = models.AutoField(primary_key=True)
    page_namespace = models.IntegerField()
    page_title = models.CharField(max_length=255)
    page_restrictions = models.TextField()
    page_counter = models.BigIntegerField()
    page_is_redirect = models.IntegerField()
    page_is_new = models.IntegerField()
    page_random = models.FloatField()
    page_touched = models.CharField(max_length=14)
    page_links_updated = models.CharField(max_length=14, blank=True, null=True)
    page_latest = models.IntegerField()
    page_len = models.IntegerField()
    page_content_model = models.CharField(max_length=32, blank=True, null=True)
    page_lang = models.CharField(max_length=35, blank=True, null=True)
    
    class Meta:
        managed = False
        db_table = 'page'
        unique_together = (('page_namespace', 'page_title'),)

    def __str__(self):
        return '({}) {}'.format(self.page_id, self.page_title)


class Pagelinks(models.Model):
    pl_from = models.IntegerField()
    pl_namespace = models.IntegerField()
    pl_title = models.CharField(max_length=255)
    pl_from_namespace = models.IntegerField()
    
    class Meta:
        managed = False
        db_table = 'pagelinks'
        unique_together = (('pl_from', 'pl_namespace', 'pl_title'),)


class Redirect(models.Model):
    rd_from = models.IntegerField(primary_key=True)
    rd_namespace = models.IntegerField()
    rd_title = models.CharField(max_length=255)
    rd_interwiki = models.CharField(max_length=32, blank=True, null=True)
    rd_fragment = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        managed = False
        db_table = 'redirect'