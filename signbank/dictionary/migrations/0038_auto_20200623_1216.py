# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2020-06-23 10:16
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dictionary', '0040_auto_20220329_1328'),
    ]

    operations = [
        migrations.RenameField(
            model_name='fieldchoice',
            old_name='english_name',
            new_name='name',
        ),
    ]
