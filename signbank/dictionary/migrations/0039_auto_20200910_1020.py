# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2020-09-10 08:20
from __future__ import unicode_literals

from django.db import migrations

from signbank.dictionary.models import Handshape, Gloss


def add_default_fieldchoices(apps, schema_editor):
    """
    Add 0 and 1 choices to every FieldChoice category
    :param apps: 
    :param schema_editor: 
    :return: 
    """
    FieldChoice = apps.get_model('dictionary', 'FieldChoice')
    for category in sorted(set(FieldChoice.objects.all().values_list('field', flat=True))):
        new_field_choice_0, created = FieldChoice.objects.get_or_create(field=category, english_name='-',
                                                                        dutch_name='-', chinese_name='-',
                                                                        machine_value=0)
        new_field_choice_1, created = FieldChoice.objects.get_or_create(field=category, english_name='N/A',
                                                                      dutch_name='N/A', chinese_name='N/A',
                                                                      machine_value=1)


def move_fieldchoice_choice_for_class(apps, schema_editor, klass):
    """
    Make a foreign key ref based on the machine_value and the category of the corresponding field
    :param apps: 
    :param schema_editor:
    :param klass: the class for which fieldchoices should be moved to foreign keys
    :return: 
    """
    klass_old = apps.get_model('dictionary', klass.__name__)
    FieldChoice = apps.get_model('dictionary', 'FieldChoice')

    fk_field_names = [f.name[:-3] for f in klass_old._meta.fields if f.name.endswith('_fk')]
    print("FIELDS:", fk_field_names)

    for obj in klass_old.objects.all():
        for field in fk_field_names:
            machine_value = getattr(obj, field)
            if machine_value:
                category = klass._meta.get_field(field+'_fk').field_choice_category
                print(klass.__name__, obj.pk,"=> Field:", field, "Category:", category, "machine_value:", machine_value)
                try:
                    field_choice = FieldChoice.objects.get(field=category, machine_value=machine_value)
                    setattr(obj, field+'_fk', field_choice)
                    obj.save()
                except:
                    print("INFO: fieldchoice not found")


def move_fieldchoice_choice(apps, schema_editor):
    move_fieldchoice_choice_for_class(apps, schema_editor, Handshape)
    move_fieldchoice_choice_for_class(apps, schema_editor, Gloss)


class Migration(migrations.Migration):

    dependencies = [
        ('dictionary', '0038_auto_20200914_1221'),
    ]

    operations = [
        migrations.RunPython(add_default_fieldchoices),
        migrations.RunPython(move_fieldchoice_choice),
    ]
