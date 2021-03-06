# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2018-05-18 12:20
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('cat_id', models.AutoField(primary_key=True, serialize=False)),
                ('cat_title', models.CharField(max_length=255, unique=True)),
                ('cat_pages', models.IntegerField()),
                ('cat_subcats', models.IntegerField()),
                ('cat_files', models.IntegerField()),
            ],
            options={
                'managed': False,
                'db_table': 'category',
            },
        ),
        migrations.CreateModel(
            name='Categorylinks',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cl_from', models.IntegerField()),
                ('cl_to', models.CharField(max_length=255)),
                ('cl_sortkey', models.CharField(max_length=230)),
                ('cl_timestamp', models.DateTimeField()),
                ('cl_sortkey_prefix', models.CharField(max_length=255)),
                ('cl_collation', models.CharField(max_length=32)),
                ('cl_type', models.CharField(max_length=6)),
            ],
            options={
                'managed': False,
                'db_table': 'categorylinks',
            },
        ),
        migrations.CreateModel(
            name='Page',
            fields=[
                ('page_id', models.AutoField(primary_key=True, serialize=False)),
                ('page_namespace', models.IntegerField()),
                ('page_title', models.CharField(max_length=255)),
                ('page_restrictions', models.TextField()),
                ('page_counter', models.BigIntegerField()),
                ('page_is_redirect', models.IntegerField()),
                ('page_is_new', models.IntegerField()),
                ('page_random', models.FloatField()),
                ('page_touched', models.CharField(max_length=14)),
                ('page_links_updated', models.CharField(blank=True, max_length=14, null=True)),
                ('page_latest', models.IntegerField()),
                ('page_len', models.IntegerField()),
                ('page_content_model', models.CharField(blank=True, max_length=32, null=True)),
                ('page_lang', models.CharField(blank=True, max_length=35, null=True)),
            ],
            options={
                'managed': False,
                'db_table': 'page',
            },
        ),
        migrations.CreateModel(
            name='Pagelinks',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pl_from', models.IntegerField()),
                ('pl_namespace', models.IntegerField()),
                ('pl_title', models.CharField(max_length=255)),
                ('pl_from_namespace', models.IntegerField()),
            ],
            options={
                'managed': False,
                'db_table': 'pagelinks',
            },
        ),
        migrations.CreateModel(
            name='Redirect',
            fields=[
                ('rd_from', models.IntegerField(primary_key=True, serialize=False)),
                ('rd_namespace', models.IntegerField()),
                ('rd_title', models.CharField(max_length=255)),
                ('rd_interwiki', models.CharField(blank=True, max_length=32, null=True)),
                ('rd_fragment', models.CharField(blank=True, max_length=255, null=True)),
            ],
            options={
                'managed': False,
                'db_table': 'redirect',
            },
        ),
        migrations.CreateModel(
            name='Hypernym',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(db_index=True, max_length=255)),
                ('value', models.TextField()),
            ],
        ),
    ]
