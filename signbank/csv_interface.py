
from signbank.dictionary.models import *
from tagging.models import Tag, TaggedItem
from signbank.dictionary.forms import *
from signbank.dictionary.consistency_senses import check_consistency_senses
from django.utils.translation import override, gettext_lazy as _, activate
from signbank.settings.server_specific import LANGUAGES, LEFT_DOUBLE_QUOTE_PATTERNS, RIGHT_DOUBLE_QUOTE_PATTERNS
from signbank.dictionary.update_senses_mapping import add_sense_to_revision_history


def add_sentence_to_revision_history(request, gloss, old_value, new_value):
    # add update sentence to revision history, indicated by both old and new values
    sentence_label = 'Sentence'
    revision = GlossRevision(old_value=old_value,
                             new_value=new_value,
                             field_name=sentence_label,
                             gloss=gloss,
                             user=request.user,
                             time=datetime.now(tz=get_current_timezone()))
    revision.save()


def create_empty_sense(gloss, order, erase=False):

    # make a new sense and translations for it
    translation_languages = gloss.lemma.dataset.translation_languages.all().order_by('id')
    sense_translations = dict()

    existing_senses = GlossSense.objects.filter(gloss=gloss, order=order)
    if existing_senses.count() > 1:
        print('create_empty_sense: multiple senses already exist: ', gloss, str(gloss.id), str(order), existing_senses)
        raise MultipleObjectsReturned
    if existing_senses:
        glosssense = existing_senses.first()
        sense_for_gloss = glosssense.sense
        for dataset_language in translation_languages:
            already_existing_sensetranslations = sense_for_gloss.senseTranslations.filter(language=dataset_language)
            if already_existing_sensetranslations.count() > 1:
                print('create_empty_sense: multiple sense translations exist for language: ', gloss, str(
                    gloss.id), str(order), glosssense, dataset_language, sense_for_gloss)
                raise MultipleObjectsReturned
            if already_existing_sensetranslations:
                existing_sensetranslation = already_existing_sensetranslations.first()
                if erase:
                    # force empty
                    for trans in existing_sensetranslation.translations.all():
                        existing_sensetranslation.translations.remove(trans)
                        trans.delete()
                sense_translations[dataset_language] = existing_sensetranslation
                continue
            glosssenselanguage = SenseTranslation(language=dataset_language)
            glosssenselanguage.save()
            sense_for_gloss.senseTranslations.add(glosssenselanguage)
            sense_translations[dataset_language] = glosssenselanguage
            continue
        return sense_for_gloss, sense_translations

    sense_for_gloss = Sense()
    sense_for_gloss.save()
    glosssense = GlossSense(gloss=gloss, sense=sense_for_gloss, order=order)
    glosssense.save()
    for dataset_language in translation_languages:
        glosssenselanguage = SenseTranslation(language=dataset_language)
        glosssenselanguage.save()
        sense_for_gloss.senseTranslations.add(glosssenselanguage)
        sense_translations[dataset_language] = glosssenselanguage
    return sense_for_gloss, sense_translations


def sense_examplesentences_for_language(gloss, language):
    # by the time this method is called, the consistency check has already been done on the Senses
    glosssenses = GlossSense.objects.filter(gloss=gloss).order_by('order')

    if not glosssenses:
        return ""
    gloss_senses = dict()
    for gs in glosssenses:
        order = gs.order
        sense = gs.sense
        if order in gloss_senses.keys():
            if settings.DEBUG_CSV:
                # if something is messed up with duplicate senses with the same number, just ignore
                print('ERROR: sense_examplesentences_for_language duplicate order: ', order)
                print(gloss, str(gloss.id), order, sense)
                continue
        gloss_senses[order] = sense

    activate(LANGUAGES[0][0])
    sentences_display_list = []
    for order in gloss_senses.keys():
        sense = gloss_senses[order]
        example_sentences = sense.exampleSentences.all()
        list_of_sentences = []
        for examplesentence in example_sentences:
            examplesentence_translations = examplesentence.examplesentencetranslation_set.filter(language=language)
            for sentence in examplesentence_translations:
                sentence_type_display = examplesentence.sentenceType.name if examplesentence.sentenceType else '-'
                sentence_tuple = (str(examplesentence.id), sentence_type_display, str(examplesentence.negative), sentence.text)
                list_of_sentences.append(sentence_tuple)
        if not list_of_sentences:
            continue
        sentences_display = []
        for (sid, stype, negative, text) in list_of_sentences:
            # does not use a comprehension because of possible nested parentheses in text fields
            tuple_reordered = '(' + str(order) + ', ' + sid + ', ' + stype + ', ' + negative + ', "' + text + '")'
            sentences_display.append(tuple_reordered)
        sorted_sentences_display = ' | '.join(sentences_display)
        sentences_display_list.append(sorted_sentences_display)
    if not sentences_display_list:
        return ""
    sentences_display = ' | '.join(sentences_display_list)
    return sentences_display


def map_values_to_sentence_type(values, include_sentences=True):
    map_errors = False
    activate(LANGUAGES[0][0])
    sentencetype_role_choices = [st.name for st in FieldChoice.objects.filter(field__iexact='SentenceType',
                                                                              machine_value__gt=1)]
    import re
    pattern_mapped_sorted_note_names = []
    for note_name in sentencetype_role_choices:
        escaped_note_name = re.sub(r'([()])', r'\\\1', note_name)
        pattern_mapped_sorted_note_names.append(escaped_note_name)

    sentence_types = '|'.join(pattern_mapped_sorted_note_names)
    if sentence_types:
        pattern_sentence_types = '(-|N/A|' + sentence_types + ')'
    else:
        pattern_sentence_types = '(-|N/A)'
    mapped_values = values

    if include_sentences:
        regex_string = (r'\s?\(([1-9]), ([1-9][0-9]*), %s, (True|False), %s([^\"]+)%s\)\s?'
                        % (pattern_sentence_types, LEFT_DOUBLE_QUOTE_PATTERNS, RIGHT_DOUBLE_QUOTE_PATTERNS))
    else:
        regex_string = r'\s?\(([1-9]), ([1-9][0-9]*), %s, (True|False)\)\s?' % pattern_sentence_types
    find_all = re.findall(regex_string, mapped_values)
    if not find_all:
        map_errors = True
    return find_all, map_errors


def get_sense_numbers(gloss):
    # by the time this method is called, the consistency check has already been done on the Senses
    glosssenses = GlossSense.objects.filter(gloss=gloss).order_by('order')

    if not glosssenses:
        return []
    gloss_senses = dict()
    for gs in glosssenses:
        order = gs.order
        sense = gs.sense
        if order in gloss_senses.keys():
            if settings.DEBUG_CSV:
                # if something is messed up with duplicate senses with the same number, just ignore
                print('ERROR: get_sense_numbers duplicate order: ', str(gloss.id), str(order))
                continue
        gloss_senses[order] = sense

    sense_numbers = [str(order) for order in gloss_senses.keys()]
    return sense_numbers


def get_senses_to_sentences(gloss):
    # by the time this method is called, the consistency check has already been done on the Senses
    glosssenses = GlossSense.objects.filter(gloss=gloss).order_by('order')

    if not glosssenses:
        return []
    gloss_senses = dict()
    gloss_senses_to_sentences_dict = dict()
    for gs in glosssenses:
        order = gs.order
        sense = gs.sense
        if order in gloss_senses.keys():
            if settings.DEBUG_CSV:
                # if something is messed up with duplicate senses with the same number, just ignore
                print('ERROR: get_sense_numbers duplicate order: ', str(gloss.id), str(order))
                continue
        gloss_senses[order] = sense
        sense_sentences = sense.exampleSentences.all()
        gloss_senses_to_sentences_dict[str(order)] = [str(sentence.id) for sentence in sense_sentences]

    return gloss_senses_to_sentences_dict


def parse_sentence_row(row_nr, sentence_dict):
    errors = []
    sentence_fields = '(' + sentence_dict['order'] + ', ' + sentence_dict['sentence_type'] + ', ' + sentence_dict['negative'] + ')'
    find_all, map_errors = map_values_to_sentence_type(sentence_fields, include_sentences=False)
    if map_errors:
        errors += ['Row '+row_nr + ': Error parsing sentence columns Sense Number, Sentence Type, Negative: '+sentence_fields]
    gloss_pk = sentence_dict['gloss_pk']
    try:
        dataset = Dataset.objects.get(acronym=sentence_dict['dataset'])
    except ObjectDoesNotExist:
        dataset = None
        errors += ['Row '+row_nr + ': Dataset '+sentence_dict['dataset']+' does not exist']
    try:
        gloss = Gloss.objects.get(pk=int(gloss_pk))
    except (ObjectDoesNotExist, ValueError, MultipleObjectsReturned):
        gloss = None
        errors += ['Row '+row_nr + ': Gloss ID '+gloss_pk+' does not exist.']
    if gloss and dataset and gloss.lemma and gloss.lemma.dataset != dataset:
        errors += ['Row '+row_nr + ': Gloss '+gloss_pk+' is not in dataset '+sentence_dict['dataset']+'.']
    if gloss:
        gloss_senses = get_sense_numbers(gloss)
        if sentence_dict['order'] not in gloss_senses:
            errors += ['Row '+row_nr + ': Gloss '+gloss_pk+' does not have a Sense Number '+sentence_dict['order']+'.']
    return errors


def update_sentences_parse(sense_numbers, sense_numbers_to_sentences, new_sentences_string):
    """CSV Import Update check the parsing of the senses field"""

    if not new_sentences_string:
        # do nothing
        return True

    new_sentences = [k for k in new_sentences_string.split(' | ')]

    new_sentence_tuples = []
    for sentence_tuple in new_sentences:
        find_all, map_errors = map_values_to_sentence_type(sentence_tuple, include_sentences=True)
        if map_errors or not find_all:
            # examine errors
            continue
        new_sentence_tuples.append(find_all[0])

    if settings.DEBUG_CSV:
        print('Parsed sentence tuples: ', new_sentence_tuples)

    sentence_ids = []
    for order, sentence_id, sentence_type, negative, sentence_text in new_sentence_tuples:
        if order not in sense_numbers:
            return False
        if order not in sense_numbers_to_sentences.keys():
            return False
        if sentence_id not in sense_numbers_to_sentences[order]:
            return False
        sentence_ids.append(sentence_id)
    if len(sentence_ids) != len(list(set(sentence_ids))):
        # updates to same sentence in two different tuples
        return False

    return True


def sentence_tuple_list_to_string(sentence_tuple_string):
    tuple_list_of_strings = []

    if not sentence_tuple_string:
        return tuple_list_of_strings
    sentences = [k for k in sentence_tuple_string.split(' | ')]
    for sentence_tuple in sentences:
        find_all, map_errors = map_values_to_sentence_type(sentence_tuple, include_sentences=True)
        if map_errors or not find_all:
            # skip any non-parsing tuples, this was already checked so should not happen
            continue
        tuple_list_of_strings.append(find_all[0])

    return tuple_list_of_strings


def csv_sentence_tuples_list_compare(gloss_id, sentence_string_old, sentence_string_new, errors_found):
    # convert input to list of tuples (order, sentence_id, sentence_type, negative, sentence_text)
    sentence_tuples_old = sentence_tuple_list_to_string(sentence_string_old)
    sentence_tuples_new = sentence_tuple_list_to_string(sentence_string_new)

    different_org = []
    different_new = []
    errors = errors_found
    original_sentences_lookup = {sid: (so, styp, sn, stxt)
                                 for (so, sid, styp, sn, stxt) in sentence_tuples_old}
    for (order, sentence_id, sentence_type, negative, sentence_text) in sentence_tuples_new:
        if (order, sentence_type, negative, sentence_text) != original_sentences_lookup[sentence_id]:
            (sord, styp, sneg, stxt) = original_sentences_lookup[sentence_id]
            if sord != order:
                errors += ['ERROR Gloss ' + gloss_id + ': The Sense Number cannot be modified in CSV Update.']
            if styp != sentence_type:
                errors += ['ERROR Gloss ' + gloss_id + ': The Sentence Type cannot be modified in CSV Update.']
            if sneg != negative:
                errors += ['ERROR Gloss ' + gloss_id + ': The Sentence Negative cannot be modified in CSV Update.']
            if errors:
                continue
            tuple_string_new = '(' + order + ', ' + sentence_id + ', ' + sentence_type \
                               + ', ' + negative + ', "' + sentence_text + '")'
            different_new.append(tuple_string_new)
            tuple_string_org = '(' + sord + ', ' + sentence_id + ', ' + styp \
                               + ', ' + sneg + ', "' + stxt + '")'
            different_org.append(tuple_string_org)
    difference_new = ' | '.join(different_new)
    difference_org = ' | '.join(different_org)
    return difference_org, difference_new, errors


def csv_update_sentences(request, gloss, language, new_sentences_string, update=False):
    """CSV Import Update the senses field"""
    # this function assumes the new_senses_string is correctly parsed
    # the function update_senses_parse tests this
    # the sense numbers in the new_senses_string are unique numbers between 1 and 9
    if settings.DEBUG_CSV:
        print('call to csv_update_sentences: ', gloss, str(gloss.id), language, new_sentences_string)
    if not new_sentences_string:
        return

    new_sentences = [k for k in new_sentences_string.split(' | ')]

    glosssenses = GlossSense.objects.filter(gloss=gloss).order_by('order')

    if not glosssenses:
        return
    gloss_senses = dict()
    for gs in glosssenses:
        order = gs.order
        sense = gs.sense
        if order in gloss_senses.keys():
            if settings.DEBUG_CSV or settings.DEBUG_SENSES:
                print('ERROR: csv_update_sentences: duplicate order: ', order)
                print('ERROR: csv_update_sentences: ', gloss, str(gloss.id), order, sense)
        gloss_senses[order] = sense

    current_sentences_string = sense_examplesentences_for_language(gloss, language)
    if settings.DEBUG_CSV:
        print('Existing sentences: ', current_sentences_string)

    new_sentence_tuples = []
    for sentence_tuple in new_sentences:
        find_all, map_errors = map_values_to_sentence_type(sentence_tuple, include_sentences=True)
        if map_errors or not find_all:
            # examine errors
            if settings.DEBUG_CSV:
                print('ERROR: Parsing error sentence tuple: ', sentence_tuple)
            continue
        new_sentence_tuples.append(find_all[0])

    activate(LANGUAGES[0][0])
    sentencetype_roles_to_type = {st.name: st
                                  for st in FieldChoice.objects.filter(field__iexact='SentenceType')}

    new_sentences_list = []
    for order, sentence_id, sentence_type, negative, sentence_text in new_sentence_tuples:
        new_sentence_dict = dict()
        new_sentence_dict['order'] = int(order)
        new_sentence_dict['sentence_id'] = int(sentence_id)
        new_sentence_dict['sentence_type'] = sentencetype_roles_to_type[sentence_type]
        new_sentence_dict['negative'] = negative == 'True'
        new_sentence_dict['sentence_text'] = sentence_text
        new_sentences_list.append(new_sentence_dict)

    if settings.DEBUG_CSV:
        print('Sentences to update: ', new_sentences_list)

    if not update:
        if settings.DEBUG_CSV:
            print('Sentences to update: update set to False')
        return

    for sentence_dict in new_sentences_list:
        # do not allow to change the sense number since this could cause inconsistencies
        # sense = gloss_senses[sentence_dict['order']]

        sentence_id = sentence_dict['sentence_id']
        try:
            examplesentence = ExampleSentence.objects.get(id=sentence_id)
            old_example_sentence = str(examplesentence)
        except (ObjectDoesNotExist, MultipleObjectsReturned):
            continue

        # do not change these since this could cause problems with language columns
        # examplesentence.negative = sentence_dict['negative']
        # examplesentence.sentenceType = sentence_dict['sentence_type']
        # examplesentence.save()

        try:
            sentence_translation = ExampleSentenceTranslation.objects.get(language=language,
                                                                          examplesentence=examplesentence)
        except ObjectDoesNotExist:
            sentence_translation = ExampleSentenceTranslation(language=language,
                                                              examplesentence=examplesentence)
        sentence_translation.text = sentence_dict['sentence_text']
        sentence_translation.save()
    new_example_sentence = str(examplesentence)
    add_sentence_to_revision_history(request, gloss, old_example_sentence, new_example_sentence)


def csv_create_sentence(request, gloss, dataset_languages, sentence_to_create, create=False):
    """CSV Import Update the senses field"""
    if settings.DEBUG_CSV:
        print('call to csv_create_sentence: ', gloss, str(gloss.id), sentence_to_create)

    glosssenses = GlossSense.objects.filter(gloss=gloss).order_by('order')

    if not glosssenses:
        return ""
    gloss_senses = dict()
    for gs in glosssenses:
        order = gs.order
        sense = gs.sense
        if order in gloss_senses.keys():
            print('ERROR: csv_update_sentences: duplicate order: ', order)
            print(gloss, str(gloss.id), order, sense)
        gloss_senses[order] = sense

    activate(LANGUAGES[0][0])
    sentencetype_roles_to_type = {st.name: st
                                  for st in FieldChoice.objects.filter(field__iexact='SentenceType')}

    new_sentence_dict = dict()
    new_sentence_dict['order'] = int(sentence_to_create['order'])
    new_sentence_dict['sentence_type'] = sentencetype_roles_to_type[sentence_to_create['sentence_type']]
    new_sentence_dict['negative'] = sentence_to_create['negative'] == 'True'

    if not create:
        if settings.DEBUG_CSV:
            print('New sentences to create: create set to False')
        return

    sense = gloss_senses[new_sentence_dict['order']]

    examplesentence = ExampleSentence(negative=new_sentence_dict['negative'],
                                      sentenceType=new_sentence_dict['sentence_type'])
    examplesentence.save()
    sense.exampleSentences.add(examplesentence, through_defaults={'order':sense.exampleSentences.count()+1})

    for language in dataset_languages:
        sentence_text = sentence_to_create['sentence_text_'+language.language_code_2char]
        sentence_translation = ExampleSentenceTranslation(language=language,
                                                          examplesentence=examplesentence,
                                                          text=sentence_text)
        sentence_translation.save()

    new_example_sentence = str(examplesentence)
    add_sentence_to_revision_history(request, gloss, "", new_example_sentence)


def sense_translations_for_language(gloss, language):
    # This finds the sense translations for one language
    # It is used for export of CSV
    # It is used again for import CSV update
    # The exact same function is used in order to identify whether a cell has been modified
    # The code is flattened out, avoiding usage of 'join' on empty lists
    # The 'join' on empty lists causes problems with spaces not matching
    # The SenseTranslation get_translations method causes problems with spaces not matching

    check_consistency_senses(gloss, delete_empty=True)
    glosssenses = GlossSense.objects.filter(gloss=gloss).order_by('order')

    if not glosssenses:
        return ""
    gloss_senses = dict()
    for gs in glosssenses:
        order = gs.order
        sense = gs.sense
        if order in gloss_senses.keys():
            print('ERROR: duplicate order: ', order)
            print(gloss, str(gloss.id), order, sense)
        gloss_senses[order] = sense

    translations_per_language = []
    for order, sense in gloss_senses.items():
        sensetranslations = sense.senseTranslations.filter(language=language)
        if not sensetranslations.count():
            if settings.DEBUG_CSV:
                print('No sensetranslation object for ', gloss, ' ( ', str(gloss.id), ') ', language)
            continue
        elif sensetranslations.count() > 1:
            if settings.DEBUG_CSV:
                print('Multiple sensetranslation objects for ', gloss, ' ( ', str(gloss.id), ') ', sensetranslations)
        sensetranslation = sensetranslations.first()
        keywords_list = []
        translations = sensetranslation.translations.all().order_by('index')
        for translation in translations:
            keywords_list.append(translation.translation.text)
        if keywords_list:
            keywords = ', '.join(keywords_list)
            sense_translations = str(order) + '. ' + keywords
            translations_per_language.append(sense_translations)
    if translations_per_language:
        sense_translations = ' | '.join(translations_per_language)
    else:
        sense_translations = ""
    if settings.DEBUG_CSV:
        print(gloss, str(gloss.id), language, sense_translations)
    return sense_translations


def update_senses_parse(new_senses_string):
    """CSV Import Update check the parsing of the senses field"""

    if not new_senses_string:
        # do nothing
        return True

    new_senses = [k for k in new_senses_string.split(' | ')]
    order_list = []
    for ns in new_senses:
        try:
            order_string, keywords_string = ns.split('. ')
        except ValueError:
            # incorrect separator between sense number and keywords
            if settings.DEBUG_CSV:
                print('first error: ', ns)
            return False
        try:
            order = int(order_string)
        except ValueError:
            # sense is not a number
            if settings.DEBUG_CSV:
                print('second error: ', ns, order_string, keywords_string)
            return False
        if order not in range(1, 9):
            # sense out of range
            if settings.DEBUG_CSV:
                print('third error: ', ns, order, keywords_string)
            return False
        if order in order_list:
            # duplicate sense number found
            if settings.DEBUG_CSV:
                print('fourth error: ', ns, order, keywords_string)
            return False
        order_list.append(order)
        if not keywords_string:
            if settings.DEBUG_CSV:
                # no keywords specified
                print('fifth error: ', ns)
                return False
        try:
            keywords_list = keywords_string.split(', ')
        except ValueError:
            if settings.DEBUG_CSV:
                print('sixth error: ', ns, order, keywords_string)
            return False
        if len(keywords_list) != len(list(set(keywords_list))):
            # duplicates in same sense
            if settings.DEBUG_CSV:
                print('seventh error: ', ns, order, keywords_list)
            return False

    return True


def sense_translations_for_language_mapping(gloss, language):

    sense_keywords_mapping = dict()
    glosssenses = GlossSense.objects.all().prefetch_related('sense').filter(gloss=gloss).order_by('order')
    if not glosssenses:
        return sense_keywords_mapping

    gloss_senses = dict()
    for gs in glosssenses:
        gloss_senses[gs.order] = gs.sense
    for order, sense in gloss_senses.items():
        sensetranslations = sense.senseTranslations.filter(language=language)
        if not sensetranslations.count():
            if settings.DEBUG_CSV:
                print('No sensetranslation object for ', gloss, ' ( ', str(gloss.id), ') ', language)
            continue
        elif sensetranslations.count() > 1:
            if settings.DEBUG_CSV:
                print('Multiple sensetranslation objects for ', gloss, ' ( ', str(gloss.id), ') ', sensetranslations)
        sensetranslation = sensetranslations.first()
        keywords_list = []
        translations = sensetranslation.translations.all().order_by('index')
        for translation in translations:
            keywords_list.append(translation.translation.text)
        if keywords_list:
            sense_keywords_mapping[order] = keywords_list
    if settings.DEBUG_CSV:
        print('sense_translations_for_language_mapping: ', gloss, str(gloss.id), language, sense_keywords_mapping)
    return sense_keywords_mapping


def csv_create_senses(request, gloss, language, new_senses_string, create=False):
    """CSV Import Update the senses field"""
    # this function assumes the new_senses_string is correctly parsed
    # the function update_senses_parse tests this
    # the sense numbers in the new_senses_string are unique numbers between 1 and 9
    # the request argument is needed to save the user sense creation in the Gloss Revision History
    if settings.DEBUG_CSV:
        print('call to csv_create_senses: ', gloss, str(gloss.id), language, '"', new_senses_string, '"')
    if not new_senses_string:
        return

    current_senses_string = sense_translations_for_language(gloss, language)
    if current_senses_string:
        # update of senses is not done by this method
        return

    new_senses = [k.strip() for k in new_senses_string.split(' | ')]

    new_senses_dict = dict()
    for ns in new_senses:
        order_string, keywords_string = ns.split('. ')
        keywords_list_split = keywords_string.split(', ')
        keywords_list = [kw.strip() for kw in keywords_list_split]
        new_senses_dict[int(order_string)] = keywords_list

    if settings.DEBUG_CSV:
        print('new senses to create: ', new_senses_dict)
    gloss_senses = GlossSense.objects.filter(gloss=gloss)

    if not gloss_senses:
        # there are currently no senses for this gloss, create an empty 1st one
        # in case the user has started numbering at something other than 1, get this
        new_senses_orders = sorted(ns for ns in new_senses_dict.keys())
        if settings.DEBUG_CSV:
            print('new sense orders: ', new_senses_orders)
        if create:
            if settings.DEBUG_CSV:
                print('csv_create_senses create: ', gloss, new_senses_string, new_senses_orders)
            # there are currently no senses for this gloss
            create_empty_sense(gloss, new_senses_orders[0], erase=True)

    if not create:
        return

    revisions = []
    for order, keywords in new_senses_dict.items():
        sense, sense_translations = create_empty_sense(gloss, order, erase=False)
        gloss_sense_translation = sense_translations[language]
        for inx, keyword in enumerate(keywords, 1):
            (keyword_object, created) = Keyword.objects.get_or_create(text=keyword)
            translation = Translation.objects.create(gloss=gloss,
                                                     language=language,
                                                     orderIndex=order,
                                                     translation=keyword_object,
                                                     index=inx)
            translation.save()
            gloss_sense_translation.translations.add(translation)
        sense_new_value = str(sense)
        revisions.append(('', sense_new_value))

    for sense_old_value, sense_new_value in revisions:
        add_sense_to_revision_history(request, gloss, sense_old_value, sense_new_value)


def csv_header_row_glosslist(dataset_languages, fields):

    lang_attr_name = 'name_' + DEFAULT_KEYWORDS_LANGUAGE['language_code_2char']
    annotationidglosstranslation_fields = ["Annotation ID Gloss" + " (" + getattr(language, lang_attr_name) + ")"
                                           for language in dataset_languages]
    lemmaidglosstranslation_fields = ["Lemma ID Gloss" + " (" + getattr(language, lang_attr_name) + ")"
                                      for language in dataset_languages]

    keyword_fields = ["Senses" + " (" + getattr(language, lang_attr_name) + ")"
                      for language in dataset_languages]

    sentence_fields = ["Example Sentences" + " (" + getattr(language, lang_attr_name) + ")"
                       for language in dataset_languages]

    # CSV should be the first language in the settings
    activate(LANGUAGES[0][0])
    header = ['Signbank ID', 'Dataset'] + lemmaidglosstranslation_fields + annotationidglosstranslation_fields \
        + keyword_fields + sentence_fields + [f.verbose_name.encode('ascii', 'ignore').decode() for f in fields]
    for extra_column in ['SignLanguages', 'Dialects', 'Sequential Morphology', 'Simultaneous Morphology',
                         'Blend Morphology',
                         'Relations to other signs', 'Relations to foreign signs', 'Tags', 'Notes']:
        header.append(extra_column)

    return header


def csv_gloss_to_row(gloss, dataset_languages, fields):

    row = [str(gloss.pk), gloss.lemma.dataset.acronym]
    for language in dataset_languages:
        lemmaidglosstranslations = gloss.lemma.lemmaidglosstranslation_set.filter(language=language)
        if lemmaidglosstranslations and len(lemmaidglosstranslations) == 1:
            # get rid of any invisible characters at the end such as \t
            lemmatranslation = lemmaidglosstranslations.first().text.strip()
            row.append(lemmatranslation)
        else:
            row.append("")
    for language in dataset_languages:
        annotationidglosstranslations = gloss.annotationidglosstranslation_set.filter(language=language)
        if annotationidglosstranslations and len(annotationidglosstranslations) == 1:
            # get rid of any invisible characters at the end such as \t
            annotation = annotationidglosstranslations.first().text.strip()
            row.append(annotation)
        else:
            row.append("")

    # Put senses (keywords) per language in a cell
    for language in dataset_languages:
        gloss_senses_of_language = sense_translations_for_language(gloss, language)
        row.append(gloss_senses_of_language)

    # Put example sentences per language in a cell
    for language in dataset_languages:
        gloss_example_sentences_of_language = sense_examplesentences_for_language(gloss, language)
        row.append(gloss_example_sentences_of_language)

    for f in fields:
        # Try the value of the choicelist
        if hasattr(f, 'field_choice_category'):
            if hasattr(gloss, 'get_' + f.name + '_display'):
                value = getattr(gloss, 'get_' + f.name + '_display')()
            else:
                field_value = getattr(gloss, f.name)
                value = field_value.name if field_value else '-'
        elif isinstance(f, models.ForeignKey) and f.related_model == Handshape:
            handshape_field_value = getattr(gloss, f.name)
            value = handshape_field_value.name if handshape_field_value else '-'
        elif f.related_model == SemanticField:
            value = ", ".join([str(sf.name) for sf in gloss.semField.all()])
        elif f.related_model == DerivationHistory:
            value = ", ".join([str(sf.name) for sf in gloss.derivHist.all()])
        else:
            value = getattr(gloss, f.name)

        # some legacy glosses have empty text fields of other formats
        if (f.__class__.__name__ == 'CharField' or f.__class__.__name__ == 'TextField') \
                and value in ['-', '------', ' ']:
            value = ''

        if value is None:
            if f.name in settings.HANDEDNESS_ARTICULATION_FIELDS:
                value = 'Neutral'
            elif f.name in settings.HANDSHAPE_ETYMOLOGY_FIELDS:
                value = 'False'
            else:
                if hasattr(f, 'field_choice_category'):
                    value = '-'
                elif f.__class__.__name__ == 'CharField' or f.__class__.__name__ == 'TextField':
                    value = ''
                elif f.__class__.__name__ == 'IntegerField':
                    value = 0
                else:
                    # what to do here? leave it as None or use empty string (for export to csv)
                    value = ''

        if not isinstance(value, str):
            # this is needed for csv
            value = str(value)

        row.append(value)

    # get languages
    signlanguages = [signlanguage.name for signlanguage in gloss.signlanguage.all()]
    row.append(", ".join(signlanguages))

    # get dialects
    dialects = [dialect.name for dialect in gloss.dialect.all()]
    row.append(", ".join(dialects))

    # get morphology
    # Sequential Morphology
    morphemes = [morpheme.get_role() + ':' + str(morpheme.morpheme.id) for morpheme in
                 MorphologyDefinition.objects.filter(parent_gloss=gloss)]
    row.append(", ".join(morphemes))

    # Simultaneous Morphology
    morphemes = [(str(m.morpheme.id), m.role) for m in gloss.simultaneous_morphology.all()]
    sim_morphs = []
    for m in morphemes:
        sim_morphs.append(':'.join(m))
    simultaneous_morphemes = ', '.join(sim_morphs)
    row.append(simultaneous_morphemes)

    # Blend Morphology
    ble_morphemes = [(str(m.glosses.id), m.role) for m in gloss.blend_morphology.all()]
    ble_morphs = []
    for m in ble_morphemes:
        ble_morphs.append(':'.join(m))
    blend_morphemes = ', '.join(ble_morphs)
    row.append(blend_morphemes)

    # get relations to other signs
    relations = [(relation.role, str(relation.target.id)) for relation in Relation.objects.filter(source=gloss)]
    relations_with_categories = []
    for rel_cat in relations:
        relations_with_categories.append(':'.join(rel_cat))

    relations_categories = ", ".join(relations_with_categories)
    row.append(relations_categories)

    # get relations to foreign signs
    relations = [(str(relation.loan), relation.other_lang, relation.other_lang_gloss) for relation in
                 RelationToForeignSign.objects.filter(gloss=gloss)]
    relations_with_categories = []
    for rel_cat in relations:
        relations_with_categories.append(':'.join(rel_cat))

    relations_categories = ", ".join(relations_with_categories)
    row.append(relations_categories)

    # export tags
    tags_of_gloss = TaggedItem.objects.filter(object_id=gloss.id)
    tag_names_of_gloss = []
    for t_obj in tags_of_gloss:
        tag_id = t_obj.tag_id
        tag_name = Tag.objects.get(id=tag_id)
        tag_names_of_gloss += [str(tag_name).replace('_', ' ')]

    tag_names = ", ".join(tag_names_of_gloss)
    row.append(tag_names)

    # export notes
    notes_of_gloss = gloss.definition_set.all()

    notes_list = []
    for note in notes_of_gloss:
        notes_list += [note.note_tuple()]
    sorted_notes_list = sorted(notes_list, key=lambda x: (x[0], x[1], x[2], x[3]))

    notes_list = []
    for (role, published, count, text) in sorted_notes_list:
        # does not use a comprehension because of nested parentheses in role and text fields
        tuple_reordered = role + ': (' + published + ',' + count + ',' + text + ')'
        notes_list.append(tuple_reordered)

    notes_display = ", ".join(notes_list)
    row.append(notes_display)

    # Make it safe for weird chars
    safe_row = []
    for column in row:
        try:
            safe_row.append(column.encode('utf-8').decode())
        except AttributeError:
            safe_row.append(None)

    return safe_row


def csv_header_row_morphemelist(dataset_languages, fields):

    lang_attr_name = 'name_' + DEFAULT_KEYWORDS_LANGUAGE['language_code_2char']
    annotationidglosstranslation_fields = ["Annotation ID Gloss" + " (" + getattr(language, lang_attr_name) + ")"
                                           for language in dataset_languages]

    # TO DO: make multilingual columns
    keyword_fields = ["Keywords" + " (" + getattr(language, lang_attr_name) + ")"
                      for language in dataset_languages]

    with override(LANGUAGE_CODE):
        header = ['Signbank ID'] + annotationidglosstranslation_fields + [f.verbose_name.title().encode('ascii', 'ignore').decode() for f in fields]

    for extra_column in ['Keywords', 'Morphology', 'Appears in signs']:
        header.append(extra_column)

    return header


def csv_morpheme_to_row(gloss, dataset_languages, fields):

    row = [str(gloss.pk)]

    for language in dataset_languages:
        annotationidglosstranslations = gloss.annotationidglosstranslation_set.filter(language=language)
        if annotationidglosstranslations and len(annotationidglosstranslations) == 1:
            row.append(annotationidglosstranslations[0].text)
        else:
            row.append("")

    for f in fields:
        # Try the value of the choicelist
        if hasattr(f, 'field_choice_category'):
            if hasattr(gloss, 'get_' + f.name + '_display'):
                value = getattr(gloss, 'get_' + f.name + '_display')()
            else:
                field_value = getattr(gloss, f.name)
                value = field_value.name if field_value else '-'
        elif isinstance(f, models.ForeignKey) and f.related_model == Handshape:
            handshape_field_value = getattr(gloss, f.name)
            value = handshape_field_value.name if handshape_field_value else '-'
        elif f.related_model == SemanticField:
            value = ", ".join([str(sf.name) for sf in gloss.semField.all()])
        elif f.related_model == DerivationHistory:
            value = ", ".join([str(sf.name) for sf in gloss.derivHist.all()])
        else:
            value = getattr(gloss, f.name)
            value = str(value)

        row.append(value)

    # get translations
    trans = [t.translation.text for t in gloss.translation_set.all().order_by('index')]
    row.append(", ".join(trans))

    # get compound's component type
    morphemes = [morpheme.role for morpheme in MorphologyDefinition.objects.filter(parent_gloss=gloss)]
    row.append(", ".join(morphemes))

    # Got all the glosses (=signs) this morpheme appears in
    appearsin = [appears.idgloss for appears in MorphologyDefinition.objects.filter(parent_gloss=gloss)]
    row.append(", ".join(appearsin))

    # Make it safe for weird chars
    safe_row = []
    for column in row:
        try:
            safe_row.append(column.encode('utf-8').decode())
        except AttributeError:
            safe_row.append(None)

    return safe_row


def csv_header_row_handshapelist(fields):

    activate(LANGUAGES[0][0])
    header = ['Handshape ID'] + [f.verbose_name.encode('ascii', 'ignore').decode().capitalize()
                                 for f in fields]

    return header


def csv_handshape_to_row(handshape, fields):

    row = [str(handshape.pk)]

    for f in fields:
        # Try the value of the choicelist
        if hasattr(f, 'field_choice_category'):
            if hasattr(handshape, 'get_' + f.name + '_display'):
                value = getattr(handshape, 'get_' + f.name + '_display')()
            else:
                value = getattr(handshape, f.name)
                if value is not None:
                    value = value.name
        else:
            value = getattr(handshape, f.name)

        if not isinstance(value, str):
            value = str(value)

        if value is None:
            if f.__class__.__name__ == 'CharField' or f.__class__.__name__ == 'TextField':
                value = ''
            elif f.__class__.__name__ == 'IntegerField':
                value = 0
            else:
                value = ''

        row.append(value)

    # Make it safe for weird chars
    safe_row = []
    for column in row:
        try:
            safe_row.append(column.encode('utf-8').decode())
        except AttributeError:
            safe_row.append(None)

    return safe_row

