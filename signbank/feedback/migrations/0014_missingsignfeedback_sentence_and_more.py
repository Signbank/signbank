# Generated by Django 4.2.11 on 2024-06-14 11:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feedback', '0013_remove_signfeedback_translation'),
    ]

    operations = [
        migrations.AddField(
            model_name='missingsignfeedback',
            name='sentence',
            field=models.FileField(blank=True, upload_to='upload'),
        ),
        migrations.AlterField(
            model_name='missingsignfeedback',
            name='video',
            field=models.FileField(blank=True, upload_to='upload'),
        ),
    ]