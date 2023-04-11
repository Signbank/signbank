# Generated by Django 4.1.7 on 2023-03-30 13:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dictionary', '0064_alter_definition_role_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='queryparametermultilingual',
            name='fieldName',
            field=models.CharField(choices=[('glosssearch', 'glosssearch'), ('lemma', 'lemma'), ('keyword', 'keyword'), ('tags', 'tags')], max_length=20, verbose_name='Text Search Field'),
        ),
    ]