"""Convert gloss videos to mp4."""

import os
import shutil
from django.core.management.base import BaseCommand
from django.core.exceptions import *
from signbank.settings.server_specific import WRITABLE_FOLDER, GLOSS_VIDEO_DIRECTORY, BACKUP_VIDEOS_FOLDER
from signbank.dictionary.models import Dataset
from signbank.video.models import GlossVideo, GlossVideoNME, GlossVideoPerspective
from signbank.dataset_checks import gloss_backup_videos, rename_backup_videos


def get_two_letter_dir(idgloss):
    foldername = idgloss[:2]

    if len(foldername) == 1:
        foldername += '-'

    return foldername


def move_video_to_folder(gloss, glossvideo, filename):
    if 'glossvideo' in filename:
        return
    # this is for when the video is not in the correct folder, compute its relative path
    idgloss = gloss.idgloss
    two_letter_dir = get_two_letter_dir(idgloss)
    dataset_dir = gloss.lemma.dataset.acronym
    desired_filename = os.path.join(GLOSS_VIDEO_DIRECTORY, dataset_dir, two_letter_dir, filename)
    source = os.path.join(WRITABLE_FOLDER, filename)
    destination = os.path.join(WRITABLE_FOLDER, GLOSS_VIDEO_DIRECTORY, dataset_dir, two_letter_dir, filename)
    print('rename_backup_videos move ', source, destination)
    os.rename(source, destination)
    glossvideo.videofile.name = desired_filename
    glossvideo.save()


class Command(BaseCommand):
    help = 'Rename gloss backup videos that have bak sequences.'

    def add_arguments(self, parser):
        parser.add_argument('dataset-acronym', nargs='+', type=str)

    def handle(self, *args, **kwargs):
        if 'dataset-acronym' in kwargs:
            for dataset_acronym in kwargs['dataset-acronym']:
                try:
                    dataset = Dataset.objects.get(acronym=dataset_acronym)
                    backup_videos = gloss_backup_videos(dataset)
                    # use a separate variable because we are going to filter out objects without a file
                    gloss_videos_to_move = backup_videos
                    checked_gloss_videos = []
                    for gloss, glossvideos in gloss_videos_to_move:
                        gloss_video_objects = glossvideos
                        checked_videos_for_gloss = []
                        for gloss_video in gloss_video_objects:
                            source = os.path.join(WRITABLE_FOLDER, str(gloss_video.videofile))
                            if not os.path.exists(source):
                                # skip non-existent files, don't put them in enumeration list
                                continue
                            checked_videos_for_gloss.append(gloss_video)
                        checked_gloss_videos.append((gloss, checked_videos_for_gloss))
                    for gloss, glossvideos in checked_gloss_videos:
                        for gv in glossvideos:
                            source = str(gv.videofile)
                            if 'glossvideo' not in source:
                                move_video_to_folder(gloss, gv, source)
                        rename_backup_videos(gloss, glossvideos)
                except ObjectDoesNotExist as e:
                    print("Dataset '{}' not found.".format(dataset_acronym), e)