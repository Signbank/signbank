
from signbank.dictionary.models import *
from signbank.dictionary.update_senses_mapping import check_consistency_senses

def create_empty_sense(gloss, order):

    # make a new sense and translations for it
    translation_languages = gloss.lemma.dataset.translation_languages.all().order_by('id')
    sense_translations = dict()
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


def update_senses(gloss, language, new_senses_string):
    """CSV Import Update the senses field"""
    # this function assumes the new_senses_string is correctly parsed
    # the function update_senses_parse tests this
    # the sense numbers in the new_senses_string are unique numbers between 1 and 9
    if settings.DEBUG_CSV:
        print('call to update_senses: ', gloss, str(gloss.id), language, new_senses_string)
    if not new_senses_string:
        return

    new_senses = [k for k in new_senses_string.split(' | ')]

    new_senses_dict = dict()
    for ns in new_senses:
        order_string, keywords_string = ns.split('. ')
        keywords_list = keywords_string.split(', ')
        new_senses_dict[int(order_string)] = keywords_list
    print('new senses: ', new_senses_dict)

    gloss_senses = GlossSense.objects.filter(gloss=gloss)

    for gs in gloss_senses:
        print('gloss sense: ', gs.gloss.id, gs.order, gs.gloss, gs.sense)
    if gloss_senses:
        # there are currently no senses for this gloss, create an empty 1st one
        # in case the user has started numbering at something other than 1, get this
        new_senses_orders = sorted(ns for ns in new_senses_dict.keys())
        print('new sense orders: ', new_senses_orders)
        create_empty_sense(gloss, new_senses_orders[0])

    original_senses_dict = sense_translations_for_language_mapping(gloss, language)

    updated_senses = dict()
    new_senses = dict()
    tentative_deleted_senses = dict()

    for order in original_senses_dict.keys():
        if order in new_senses_dict.keys():
            if original_senses_dict[order] != new_senses_dict[order]:
                updated_senses[order] = new_senses_dict[order]
        else:
            tentative_deleted_senses[order] = original_senses_dict[order]

    for order in new_senses_dict.keys():
        if order not in original_senses_dict.keys():
            new_senses[order] = new_senses_dict[order]

    print('updated: ', updated_senses)
    print('new: ', new_senses)
    print('tentative deleted: ', tentative_deleted_senses)

    regrouped_keywords = dict()
    deleted_senses = dict()
    for deleted_order, deleted_keywords_list in tentative_deleted_senses.items():
        regrouped_keywords[deleted_order] = dict()
        tentative_deleted_keywords_list = []
        for deleted_keyword in deleted_keywords_list:
            for new_order, new_keywords_list in new_senses.items():
                if deleted_keyword in new_keywords_list:
                    regrouped_keywords[deleted_order][new_order] = deleted_keyword
                else:
                    tentative_deleted_keywords_list.append(deleted_keyword)
        deleted_senses[deleted_order] = tentative_deleted_keywords_list

    print('regrouped: ', regrouped_keywords)
    print('deleted: ', deleted_senses)

    # for order, keywords in new_senses.items():
    #     sense, sense_translations = create_empty_sense(gloss, order)
    #     gloss_sense_translation = sense_translations[language]
    #     for inx, keyword in enumerate(keywords):
    #         (keyword_object, created) = Keyword.objects.get_or_create(text=keyword)
    #         translation = Translation.objects.create(gloss=gloss,
    #                                                  language=language,
    #                                                  orderIndex=order,
    #                                                  translation=keyword_object,
    #                                                  index=inx+1)
    #         translation.save()
    #         gloss_sense_translation.translations.add(translation)
    #
    # for order, keywords in updated_senses.items():
    #     sense, sense_translations = create_empty_sense(gloss, order)
    #     gloss_sense_translation = sense_translations[language]
    #     existing_translations = gloss_sense_translation.translations.all()
    #     existing_keywords = [et.translation.text for et in existing_translations]
    #     for translation in existing_translations:
    #         if translation.translation.text in existing_keywords:
    #             print('keep existing keyword')
    #             # this keyword wasn't changed
    #             continue
    #         gloss_sense_translation.translations.remove(translation)
    #         translation.delete()
    #     for inx, keyword in enumerate(keywords):
    #         if keyword in existing_keywords:
    #             # this keyword already exists
    #             print('already existing keyword: ', keyword)
    #             continue
    #         (keyword_object, created) = Keyword.objects.get_or_create(text=keyword)
    #         translation = Translation.objects.create(gloss=gloss,
    #                                                  language=language,
    #                                                  orderIndex=order,
    #                                                  translation=keyword_object,
    #                                                  index=inx+1)
    #         translation.save()
    #         gloss_sense_translation.translations.add(translation)
    #
    # for order, keywords in deleted_senses.items():
    #     gloss_sense = GlossSense.objects.filter(gloss=gloss, order=order).first()
    #     if not gloss_sense:
    #         continue
    #     sense = gloss_sense.sense
    #     gloss_sense_translation = sense.senseTranslations.filter(language=language).first()
    #     if gloss_sense_translation:
    #         existing_keywords = gloss_sense_translation.translations.all()
    #         for translation in existing_keywords:
    #             gloss_sense_translation.translations.remove(translation)
    #             translation.delete()
    #         sense.senseTranslations.remove(gloss_sense_translation)
    #         gloss_sense_translation.delete()
    #     if not sense.senseTranslations():
    #         sense.delete()
    #         gloss_sense.delete()

    return