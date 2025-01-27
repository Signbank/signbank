from django.contrib import admin
from django import forms
from django.db import models
from signbank.video.models import GlossVideo, GlossVideoHistory, AnnotatedVideo, ExampleVideoHistory
from signbank.dictionary.models import Dataset, AnnotatedGloss
from django.contrib.auth.models import User
from signbank.settings.base import *
from signbank.settings.server_specific import WRITABLE_FOLDER, FILESYSTEM_SIGNBANK_GROUPS
from django.utils.translation import override, gettext_lazy as _
from django.db.models import Q, Count, CharField, TextField, Value as V


class GlossVideoDatasetFilter(admin.SimpleListFilter):

    title = _('Dataset')
    parameter_name = 'videos_per_dataset'

    def lookups(self, request, model_admin):
        datasets = Dataset.objects.all()
        return (tuple(
            (dataset.id, dataset.acronym) for dataset in datasets
        ))

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(gloss__lemma__dataset_id=self.value())
        return queryset.all()


class GlossVideoFileSystemGroupFilter(admin.SimpleListFilter):

    title = _('File System Group')
    parameter_name = 'filesystem_group'

    def lookups(self, request, model_admin):
        filesystem_groups = tuple((g, g) for g in FILESYSTEM_SIGNBANK_GROUPS)
        return filesystem_groups

    def queryset(self, request, queryset):

        def matching_file_group(videofile, key):
            if not key:
                return False
            from pathlib import Path
            video_file_full_path = Path(WRITABLE_FOLDER, videofile)
            if video_file_full_path.exists():
                return video_file_full_path.group() == key
            else:
                return False

        queryset_res = queryset.values('id', 'videofile')
        results = [qv['id'] for qv in queryset_res
                   if matching_file_group(qv['videofile'], self.value())]

        if self.value():
            return queryset.filter(id__in=results)
        else:
            return queryset.all()


class GlossVideoExistenceFilter(admin.SimpleListFilter):

    title = _('File Exists')
    parameter_name = 'file_exists'

    def lookups(self, request, model_admin):
        file_exists = tuple((b, b) for b in ('True', 'False'))
        return file_exists

    def queryset(self, request, queryset):

        def matching_file_exists(videofile, key):
            if not key:
                return False
            from pathlib import Path
            video_file_full_path = Path(WRITABLE_FOLDER, videofile)
            if video_file_full_path.exists():
                return key == 'True'
            else:
                return key == 'False'

        queryset_res = queryset.values('id', 'videofile')
        results = [qv['id'] for qv in queryset_res
                   if matching_file_exists(qv['videofile'], self.value())]

        if self.value():
            return queryset.filter(id__in=results)
        else:
            return queryset.all()


class GlossVideoAdmin(admin.ModelAdmin):

    list_display = ['id', 'gloss', 'video_file', 'perspective', 'NME', 'file_timestamp', 'file_group', 'permissions', 'file_size', 'version']
    list_filter = (GlossVideoDatasetFilter, GlossVideoFileSystemGroupFilter, GlossVideoExistenceFilter)

    search_fields = ['^gloss__annotationidglosstranslation__text']

    def video_file(self, obj=None):
        # this will display the full path in the list view
        if obj is None:
            return ""
        import os
        video_file_full_path = os.path.join(WRITABLE_FOLDER, str(obj.videofile))

        return video_file_full_path

    def perspective(self, obj=None):
        if obj is None:
            return ""
        return obj.is_glossvideoperspective() is True

    def NME(self, obj=None):
        if obj is None:
            return ""
        return obj.is_glossvideonme() is True

    def file_timestamp(self, obj=None):
        # if the file exists, this will display its timestamp in the list view
        if obj is None:
            return ""
        import os
        import datetime
        video_file_full_path = os.path.join(WRITABLE_FOLDER, str(obj.videofile))
        if os.path.exists(video_file_full_path):
            return datetime.datetime.fromtimestamp(os.path.getctime(video_file_full_path))
        else:
            return ""

    def file_group(self, obj=None):
        # this will display a group in the list view
        if obj is None:
            return ""
        else:
            from pathlib import Path
            video_file_full_path = Path(WRITABLE_FOLDER, str(obj.videofile))
            if video_file_full_path.exists():
                group = video_file_full_path.group()
                return group
            else:
                return ""

    def file_size(self, obj=None):
        # this will display a group in the list view
        if obj is None:
            return ""
        else:
            from pathlib import Path
            video_file_full_path = Path(WRITABLE_FOLDER, str(obj.videofile))
            if video_file_full_path.exists():
                size = str(video_file_full_path.stat().st_size)
                return size
            else:
                return ""

    def permissions(self, obj=None):
        # this will display a group in the list view
        if obj is None:
            return ""
        else:
            from pathlib import Path
            import stat
            video_file_full_path = Path(WRITABLE_FOLDER, str(obj.videofile))
            if video_file_full_path.exists():
                stats = stat.filemode(video_file_full_path.stat().st_mode)
                return stats
            else:
                return ""

    def get_list_display_links(self, request, list_display):
        # do not allow the user to view individual revisions in list
        self.list_display_links = (None, )
        return self.list_display_links

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        if not self.file_timestamp(obj):
            return True
        return False


class GlossVideoHistoryDatasetFilter(admin.SimpleListFilter):

    title = _('Dataset')
    parameter_name = 'videos_per_dataset'

    def lookups(self, request, model_admin):
        datasets = Dataset.objects.all()
        return (tuple(
            (dataset.id, dataset.acronym) for dataset in datasets
        ))

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(gloss__lemma__dataset_id=self.value())
        return queryset.all()


class GlossVideoHistoryActorFilter(admin.SimpleListFilter):

    title = _('Actor')
    parameter_name = 'videos_per_actor'

    def lookups(self, request, model_admin):
        users = User.objects.all().distinct().order_by('first_name')
        return (tuple(
            (user.id, user.username) for user in users
        ))

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(actor__id=self.value())
        return queryset.all()


class GlossVideoHistoryAdmin(admin.ModelAdmin):

    list_display = ['action', 'datestamp', 'uploadfile', 'goal_location', 'actor', 'gloss']
    list_filter = (GlossVideoHistoryDatasetFilter, GlossVideoHistoryActorFilter)

    search_fields = ['^gloss__annotationidglosstranslation__text']


class AnnotatedVideoDatasetFilter(admin.SimpleListFilter):

    title = _('Dataset')
    parameter_name = 'dataset'

    def lookups(self, request, model_admin):
        datasets = Dataset.objects.all()
        return (tuple(
            (dataset.id, dataset.acronym) for dataset in datasets
        ))

    def queryset(self, request, queryset):
        if self.value():
            annotated_glosses = AnnotatedGloss.objects.filter(gloss__lemma__dataset_id=self.value())
            annotated_sentences_ids = [ag.annotatedsentence.id for ag in annotated_glosses]
            if not annotated_sentences_ids:
                return None
            return queryset.filter(annotatedsentence_id__in=annotated_sentences_ids)
        return queryset.all()

class AnnotatedVideoAdmin(admin.ModelAdmin):
    actions = None
    list_display = ('dataset', 'annotated_sentence', 'video_file', 'timestamp', 'eaf_file', 'eaf_timestamp', 'url', 'source')
    search_fields = ['annotatedsentence__annotated_sentence_translations__text']

    class Media:
        css = {
            'all': ('css/custom_admin.css',)
        }

    def dataset(self, obj=None):
        if obj is None:
            return ""
        annotated_glosses = AnnotatedGloss.objects.filter(annotatedsentence=obj.annotatedsentence)
        if not annotated_glosses:
            return ""
        dataset = annotated_glosses.first().gloss.lemma.dataset
        return dataset.acronym

    def annotated_sentence(self, obj=None):
        if obj is None:
            return ""
        translations = obj.annotatedsentence.get_annotatedstc_translations()
        return " | ".join(translations)

    def video_file(self, obj=None):
        if obj is None:
            return ""

        return str(obj.videofile.name)

    def timestamp(self, obj=None):
        # if the file exists, this will display its timestamp in the list view
        if obj is None:
            return ""
        import os
        import datetime
        video_file_full_path = os.path.join(WRITABLE_FOLDER, str(obj.videofile))
        if os.path.exists(video_file_full_path):
            return datetime.datetime.fromtimestamp(os.path.getctime(video_file_full_path))
        else:
            return ""

    def eaf_file(self, obj=None):
        if obj is None:
            return ""
        return str(obj.eaffile.name)

    def eaf_timestamp(self, obj=None):
        # if the file exists, this will display its timestamp in the list view
        if obj is None:
            return ""
        import os
        import datetime
        eaf_file_full_path = os.path.join(WRITABLE_FOLDER, str(obj.eaffile))
        if os.path.exists(eaf_file_full_path):
            return datetime.datetime.fromtimestamp(os.path.getctime(eaf_file_full_path))
        else:
            return ""

    def get_list_display_links(self, request, list_display):
        self.list_display_links = (None, )
        return self.list_display_links


class ExampleVideoHistoryAdmin(admin.ModelAdmin):

    list_display = ['action', 'datestamp', 'uploadfile', 'goal_location', 'actor', 'examplesentence']

    search_fields = ['^examplesentence__examplesentencetranslation__text']


admin.site.register(GlossVideo, GlossVideoAdmin)
admin.site.register(GlossVideoHistory, GlossVideoHistoryAdmin)
admin.site.register(AnnotatedVideo, AnnotatedVideoAdmin)
admin.site.register(ExampleVideoHistory, ExampleVideoHistoryAdmin)

