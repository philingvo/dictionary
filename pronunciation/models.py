import os
import re
from wsgiref.util import FileWrapper
import mimetypes
from gtts import gTTS
from random import randint
from django.db import models
from django.http import StreamingHttpResponse
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import render
from django.shortcuts import redirect
from django.urls import reverse
from django.db.models import Q
from django.http import Http404
from rest_framework.response import Response
from dictionary import settings as project_settings
from dictionaries.models import Language
from datetime import datetime


class Pronunciation_Model_Manager(models.Manager):

    lang_prefix = "_lang: "
    text_prefix = "_text: "

    def get_searching_param_value(self, prefix, query):
        query_dict = query.split(prefix)
        return query_dict[1]

    def get_text_Q(self, text):
        return Q(text__icontains=text)

    def get_lang_Q(self, lang):
        return (Q(language__english_name__icontains=lang) |
                Q(language__original_name__icontains=lang) |
                Q(language__translation_name__icontains=lang))

    def get_special_pronunciation_searching_Q(self, query):
        if " + " in query:
            query_dict = query.split(" + ")
            lang = query_dict[0]
            text = query_dict[1]
            final_Q = (self.get_lang_Q(lang) & self.get_text_Q(text))
        elif query.startswith(self.lang_prefix):
            lang = self.get_searching_param_value(self.lang_prefix, query)
            final_Q = self.get_lang_Q(lang)
        elif query.startswith(self.text_prefix):
            text = self.get_searching_param_value(self.text_prefix, query)
            final_Q = self.get_text_Q(text)
        else:
            final_Q = None
        return final_Q

    def get_common_pronunciation_searching_Q(self, query):
        return (self.get_text_Q(query) | self.get_lang_Q(query))

    def get_last_searching_Q(self, query):
        return self.get_common_pronunciation_searching_Q(query)

    def search(self, query=None):
        qs = self.get_queryset()
        if query is not None:
            final_Q = self.get_special_pronunciation_searching_Q(query)
            if not final_Q:
                final_Q = self.get_last_searching_Q(query)
            qs = qs.filter(final_Q)
        return qs

class Pronunciation(models.Model):

    objects = Pronunciation_Model_Manager()
    text = models.TextField()
    language = models.ForeignKey(Language, models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    static_dir = 'static'
    media_dir = 'media'
    template_dir = 'pronunciation'
    no_launguage_audio_filename = "en No this language to pronounce a text.mp3"
    can_not_pronounce_audio_filename = "en Can't pronounce a text.mp3"
    default_text = "no text to pronounce"
    default_attachment = False
    true_list = ["T", "True", "Yes", "t", "true", "yes"]
    list_namepath = "pronunciations_list"

    # https://gtts.readthedocs.io/en/latest/module.html#localized-accents
    gtts_source_name = "GTTS"
    gtts_localized_accents = {
                        "en":
                            (("English (Australia)", "com.au"),
                            ("English (United Kingdom)", "co.uk"),
                            ("English (United States)", "com"),
                            ("English (Canada)", "ca"),
                            ("English (India)", "co.in"),
                            ("English (Ireland)", "ie"),
                            ("English (South Africa)", "co.za")),

                        "fr":
                            (("French (Canada)", "ca"),
                            ("French (France)", "fr")),

                        "pt":
                            (("Portuguese (Brazil)", "com.br"),
                            ("Portuguese (Portugal)", "pt")),

                        "es":
                            (("Spanish (Mexico)", "com.mx"),
                            ("Spanish (Spain)", "es"),
                            ("Spanish (United States)", "com")),

                        "zh":
                            (("Mandarin (China Mainland)", None, "zh-CN"),
                            ("Mandarin (Taiwan)", None, "zh-TW"))
                        }
    gtts_default_accent = {
                            "en": "English (United Kingdom)",
                            "fr": "French (France)",
                            "pt": "Portuguese (Portugal)",
                            "es": "Spanish (Spain)",
                            "zh": "zh-CN"
                            }

    text_maximum_symbols_for_outputting = 50

    def __str__(self):
        return "({}) {}".format(self.language.code.upper(), self.text)

    def create_querystring(self):
        return "?text={}&lang={}".format(self.text, self.language.code.lower())

    def get_absolute_url(self):
        return reverse("pronunciation_page") + self.create_querystring()

    def get_pronounce_url(self):
        return reverse("pronounce") + self.create_querystring()

    def get_download_file_url(self):
        return self.get_pronounce_url() + "&attach=true"

    def get_random_pronounce_url(self):
        return self.get_pronounce_url() + "&random=true"

    def get_add_pronunciation_file_url(self):
        return reverse("add_pronunciation_file", kwargs={"pk": self.id})

    def get_pronunciation_files_list_url(self):
        return reverse("pronunciation_files_list", kwargs={"pk": self.id})

    def get_correct_page_url(self):
        return reverse("correct_pronunciation", kwargs={"pk": self.id})

    def get_delete_url(self):
        return reverse('delete_pronunciation', kwargs={'pk': self.id})

    def get_text_for_outputting(self):
        text = self.__str__()
        if len(text) > self.text_maximum_symbols_for_outputting:
            return "{}...".format(text[:self.text_maximum_symbols_for_outputting])
        else:
            return text

    @classmethod
    def get_add_new_pronunciation_url(self):
        return reverse('add_new_pronunciation')

    @classmethod
    def handle_request(self, request):
        if request.method == 'GET':
            text = request.GET.get("text", self.default_text).lower()
            lang = request.GET.get("lang", project_settings.default_defined_langauge_code)
            
            attachment = request.GET.get("attach")
            if attachment and attachment in self.true_list:
                attachment = True
            else:
                attachment = self.default_attachment
            
            random = request.GET.get("random")
            if random and random in self.true_list:
                random = True
            else:
                random = False

            return text, lang, attachment, random
        else:
            return self.default_text, project_settings.default_defined_langauge_code, self.default_attachment, False

    @staticmethod
    def check_language(language):
        languages = Language.objects.filter(code=language).exclude(original_name=project_settings.undefined_language_name)
        if len(languages) > 0:
            return languages[0]
        else:
            return False

    @staticmethod
    def get_file_full_path(file_local_path):
        return os.path.join(os.getcwd(), file_local_path)

    @staticmethod
    def give_away_file(full_filepath, give_as_attachment=False):
        filename = os.path.basename(full_filepath)
        response = HttpResponse(FileWrapper(open(full_filepath, 'rb')),
                                    content_type=mimetypes.guess_type(filename)[0])
        response['Content-Length'] = os.path.getsize(full_filepath)
        if give_as_attachment:
            response['Content-Disposition'] = "attachment; filename={}".format(filename)
        return response

    @classmethod
    def give_pronunciation_file(self, request):
        text, raw_language, give_as_attachment, random = self.handle_request(request)
        language = self.check_language(raw_language)
        if language:
            pronunciation_file = self.get_pronunciation_file(text, language, random)
            full_filepath = self.check_pronuncition_file(pronunciation_file)
            return self.give_away_file(full_filepath, give_as_attachment)
        else:
            return self.give_away_no_language_pronunciation_file(give_as_attachment)

    @classmethod
    def check_pronuncition_file(self, pronunciation_file):
        if pronunciation_file:
            return self.get_file_full_path(pronunciation_file.get_filepath())
        else:
            return self.get_can_not_pronounce_full_filepath()

    @staticmethod
    def give_json_full_filepath(full_filepath):
        return JsonResponse({"local_filepath": full_filepath})

    @classmethod
    def give_pronunciation_local_filepath(self, request):
        text, raw_language, give_as_attachment, random = self.handle_request(request)
        language = self.check_language(raw_language)
        if language:
            pronunciation_file = self.get_pronunciation_file(text, language, random)
            full_filepath = self.check_pronuncition_file(pronunciation_file)
        else:
            full_filepath = self.get_no_language_full_filepath()
        return self.give_json_full_filepath(full_filepath)

    def create_pronunciation_file(self):
        if self.language.code in self.gtts_default_accent:
            source = self.gtts_source_name
            accent = self.gtts_default_accent[self.language.code]
        else:
            source = accent = False
        
        return Pronunciation_File.create(self,
                                        accent,
                                        source,
                                        True)

    @classmethod
    def create_pronunciation(self, text, language):
        pronunciation = self(text=text,
                            language=language)
        pronunciation.save()
        return pronunciation

    @classmethod
    def get_pronunciation_file(self, text, language, random=False):

        def get_choosen_pronunciation_file():
            pronunciations = self.objects.filter(text=text,
                                                language=language)
            if pronunciations.count() > 0:
                pronunciation = pronunciations[0]
                if not random:
                    pronunciation_file = Pronunciation_File.get_choosen_pronunciation_file(pronunciation)
                else:
                    pronunciation_file = Pronunciation_File.get_random_pronunciation_file(pronunciation)
            else:
                pronunciation_file = create_pronunciation_and_pronunciation_file(text, language)
            return pronunciation_file

        def create_pronunciation_and_pronunciation_file(text, language):
            pronunciation = self.create_pronunciation(text, language)
            pronunciation_file = pronunciation.create_pronunciation_file()
            if not pronunciation_file:
                pronunciation.delete()
            return pronunciation_file

        pronunciation_file = get_choosen_pronunciation_file()
        if pronunciation_file:
            return pronunciation_file
        else:
            return False
    
    def get_pronunciation_filepath(self):
        pronunciation_local_filepath = self.get_file_local_path()
        return self.get_file_full_path(pronunciation_local_filepath)

    @classmethod
    def get_no_language_local_filepath(self):
        return os.path.join(self.static_dir, self.media_dir, "sounds", self.no_launguage_audio_filename)

    @classmethod
    def get_can_not_pronounce_a_text(self):
        return os.path.join(self.static_dir, self.media_dir, "sounds", self.can_not_pronounce_audio_filename)

    @classmethod
    def get_no_language_full_filepath(self):
        pronunciation_local_filepath = self.get_no_language_local_filepath()
        return self.get_file_full_path(pronunciation_local_filepath)

    @classmethod
    def get_can_not_pronounce_full_filepath(self):
        pronunciation_local_filepath = self.get_can_not_pronounce_a_text()
        return self.get_file_full_path(pronunciation_local_filepath)

    @classmethod
    def give_away_no_language_pronunciation_file(self, give_as_attachment):
        pronunciation_full_filepath = self.get_no_language_full_filepath()
        return self.give_away_file(pronunciation_full_filepath, give_as_attachment)

    @classmethod
    def get_pronunciation_page(self, request):

        def get_gtts_accent_list():
            gtts_accent_list = []
            gtts_accents_dict = dict()
            if language.code in self.gtts_localized_accents:
                gtts_localized_accents = self.gtts_localized_accents[language.code]
                for localized_accent in gtts_localized_accents:
                    pronunciation_file_id = None
                    if choosen_pronunciation_file and choosen_pronunciation_file.accent == localized_accent[0]:
                        pronunciation_file_id = choosen_pronunciation_file.id
                    accent_params = [self.gtts_source_name,
                                    localized_accent[0],
                                    pronunciation_file_id]
                    gtts_accent_list.append(accent_params)
                    gtts_accents_dict[localized_accent[0]] = accent_params
            return gtts_accent_list, gtts_accents_dict

        def get_pronunciation_list():
            pronunciation_list = []
            added_accents = set()
            for pronunciation_file in pronunciations_files:
                if pronunciation_file.accent not in gtts_accents_dict:
                    pronunciation_list.append([pronunciation_file.source,
                                                pronunciation_file.accent,
                                                pronunciation_file.id])
                else:
                    accent = gtts_accents_dict[pronunciation_file.accent]
                    accent[2] = pronunciation_file.id
                    pronunciation_list.append(accent)
                added_accents.add(pronunciation_file.accent)

            for gtts_accent in gtts_accent_list:
                if gtts_accent[1] not in added_accents:
                    pronunciation_list.append(gtts_accent)

            return pronunciation_list

        text, raw_language, give_as_attachment, random = self.handle_request(request)
        language = self.check_language(raw_language)
        if language:
            pronunciations = self.objects.filter(text=text,
                                                language=language)
            if pronunciations.count() > 0:
                pronunciation = pronunciations.order_by("-created_at")[0]
                choosen_pronunciation_file = Pronunciation_File.get_choosen_pronunciation_file(pronunciation)
                pronunciations_files = Pronunciation_File.objects.filter(pronunciation=pronunciation)
            else:
                choosen_pronunciation_file = self.get_pronunciation_file(text, language)
                pronunciation = choosen_pronunciation_file.pronunciation
                pronunciations_files = []

            gtts_accent_list, gtts_accents_dict = get_gtts_accent_list()
            pronunciation_list = get_pronunciation_list()
            return render(request,
                            os.path.join(self.template_dir, "pronunciation_page_template.html"),
                            {"pronunciation": pronunciation,
                            "pronunciation_list": pronunciation_list,
                            "choosen_pronunciation_file": choosen_pronunciation_file,
                            "title": pronunciation.get_text_for_outputting()})

    @classmethod
    def set_pronunciation_file(self, request):
        pronunciation_id = request.POST.get("pronunciation_id")
        pronunciation = self.objects.get(id=pronunciation_id)
        current_pronunciation_id = request.POST.get("current_pronunciation")
        if not ":" in current_pronunciation_id: # pronunciation_file already exists
            pronunciation_file = Pronunciation_File.objects.get(id=current_pronunciation_id)
            pronunciation_file.choose()
        else: # create a new gtts file
            current_pronunciation_list = current_pronunciation_id.split(": ")
            source = current_pronunciation_list[0]
            accent = current_pronunciation_list[1]
            pronunciation_file = Pronunciation_File.create(pronunciation,
                                                            accent,
                                                            source,
                                                            True)
            pronunciation_file.unselect_other_choosen()
        return redirect(pronunciation.get_absolute_url())

    @classmethod
    def get_adding_pronunciation_file_page(self, request, pk):
        initials = {}
        pronunciation = self.get_pronunciation(pk)
        initials = {"pronunciation": pronunciation}
        from .forms import Add_Pronunciation_File_Form
        form = Add_Pronunciation_File_Form(initials)
        return Pronunciation_File.return_adding_form(request, form, pronunciation)

    def get_pronunciation_files_queryset(self):
        return Pronunciation_File.objects.filter(pronunciation=self)

    @classmethod
    def get_pronunciation(self, pk):
        try:
            return self.objects.get(pk=pk)
        except self.DoesNotExist:
            raise Http404("{} does not exist".format(self.__name__))

    @classmethod
    def get_pronunciation_files_list(self, request, pk):
        pronunciation = self.get_pronunciation(pk)
        pronunciation_files = pronunciation.get_pronunciation_files_queryset()
        choosen_pronunciation_file = pronunciation_files.filter(choosen=True)

        return render(request,
                        os.path.join(self.template_dir, "pronunciation_files_list_template.html"),
                        {"pronunciation": pronunciation,
                        "choosen_pronunciation_file": choosen_pronunciation_file,
                        "pronunciation_files": pronunciation_files,
                        "title": "Pronunciation files for"})

    def delete(self, delete_file=False):
        pronunciation_files = self.get_pronunciation_files_queryset()
        for pronunciation_file in pronunciation_files:
            pronunciation_file.delete(False, delete_file)
        super().delete()
        return reverse("pronunciations_list")

    @classmethod
    def search(self, searching_param_value):
        return self.objects.search(searching_param_value)

class Pronunciation_File_Model_Manager(Pronunciation_Model_Manager):

    source_prefix = "_source: "
    accent_prefix = "_accent: "

    def get_text_Q(self, text):
        return Q(pronunciation__text__icontains=text)

    def get_lang_Q(self, lang):
        return (Q(pronunciation__language__english_name__icontains=lang) |
                Q(pronunciation__language__original_name__icontains=lang) |
                Q(pronunciation__language__translation_name__icontains=lang))

    def get_source_Q(self, source):
        return Q(source__icontains=source)

    def get_accent_Q(self, accent):
        return Q(accent__icontains=accent)

    def get_last_searching_Q(self, query):
        if query.startswith(self.source_prefix):
            source = self.get_searching_param_value(self.source_prefix, query)
            final_Q = self.get_source_Q(source)
        elif query.startswith(self.accent_prefix):
            accent = self.get_searching_param_value(self.accent_prefix, query)
            final_Q = self.get_accent_Q(accent)
        else:
            final_Q = self.get_common_pronunciation_searching_Q(query)
        return final_Q

class Pronunciation_File(models.Model):

    objects = Pronunciation_File_Model_Manager()
    pronunciation = models.ForeignKey(Pronunciation, models.PROTECT)
    source = models.CharField(max_length=255)
    accent = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    filename = models.TextField()
    choosen = models.IntegerField(null=False, default=False)

    static_dir = 'static'
    media_dir = 'media'
    pronunciations_dir = 'pronunciations'
    template_dir = 'pronunciation'

    undefined_template = "{} undefined"

    text_for_fileman_maximum_symbols = 50

    def __str__(self):
        name = "({}) {}".format(self.pronunciation.language.code.upper(),
                                self.pronunciation.text,)
        if self.source:
            name = "{} - {}".format(name, self.source)
        if self.accent:
            name = "{}: {}".format(name, self.accent)
        return name

    def get_play_file_url(self):
        return reverse('play_file', kwargs={'pk': self.id})

    def play_file(self):
        full_filepath = Pronunciation.get_file_full_path(self.get_filepath())
        return Pronunciation.give_away_file(full_filepath)

    def get_set_file_as_current(self):
        return reverse('set_file_as_current', kwargs={'pk': self.id})

    def get_absolute_url(self):
        return self.get_correct_page_url()

    def get_correct_page_url(self):
        return reverse("correct_pronunciation_file", kwargs={"pk": self.id})

    def set_file_as_current(self):
        self.choose()
        return redirect(self.pronunciation.get_pronunciation_files_list_url())

    def get_delete_url(self):
        return reverse('delete_pronunciation_file', kwargs={'pk': self.id})

    @classmethod
    def create(self, pronunciation, accent, source, choosen=False):
        
        language_code = pronunciation.language.code.lower()

        gtts_params_dict = {"lang": language_code,
                            "text": re.sub("[[]{}()@#$%^&*_<>~`/\\<>«»\"\n\r\t]", " ", pronunciation.text)}

        if language_code in Pronunciation.gtts_default_accent and not accent:
            accent = Pronunciation.gtts_default_accent[language_code]

        if language_code in Pronunciation.gtts_localized_accents:
            localized_accents = Pronunciation.gtts_localized_accents[language_code]
            for localized_accent in localized_accents:
                if localized_accent[0] == accent:
                    if len(localized_accent) == 2:
                        gtts_params_dict["tld"] = localized_accent[1]
                    else:
                        language_code = localized_accent[3]
                    break

        filename = self.get_filename(language_code,
                                    pronunciation.text,
                                    source,
                                    accent)

        path = self.get_file_local_path(language_code,
                                        filename)

        try:
            tts = gTTS(**gtts_params_dict)
            tts.save(path)
        except:
            return False
        else:
            if not source:
                source = self.undefined_template.format("Source")
            if not accent:
                accent = self.undefined_template.format("Accent")
            
            pronunciation_file = self(pronunciation=pronunciation,
                                    source=source,
                                    accent=accent,
                                    filename=filename,
                                    choosen=choosen)
            pronunciation_file.save()
            return pronunciation_file

    @staticmethod
    def check_dir_existance(direction):
        if not os.path.exists(direction):
            os.mkdir(direction)

    @classmethod
    def get_filename(self, language_code, text, source, accent):
        if len(text) > self.text_for_fileman_maximum_symbols:
            text = "{}... at {}".format(text[:self.text_for_fileman_maximum_symbols], datetime.now().strftime("%Y.%m.%d %H.%M.%S %Z"))
        filename = '{} {}'.format(language_code, text)
        if source and accent:
            filename = '{} ({} - {})'.format(filename, source, accent)
        elif accent:
            filename = '{} ({})'.format(filename, accent)
        filename = '{}.mp3'.format(filename)
        filename = filename.replace("?", '؟')
        return re.sub("[/\\:*«»<>[]\"\n\r\t]", " ", filename)

    @classmethod
    def get_file_local_path(self, language_code, filename):
        pronunciations_dir = os.path.join(self.static_dir, self.media_dir, self.pronunciations_dir)
        self.check_dir_existance(pronunciations_dir)
        language_dir = os.path.join(pronunciations_dir, language_code)
        self.check_dir_existance(language_dir)
        return os.path.join(language_dir, filename)

    def get_filepath(self):
        return self.get_file_local_path(self.pronunciation.language.code.lower(), self.filename)

    @classmethod
    def upload_file(self, request):
        pronunciation_id = int(request.POST.get('pronunciation'))
        pronunciation = Pronunciation.objects.get(id=pronunciation_id)
        uploaded_file = request.FILES['uploadfile']
        from .forms import Add_Pronunciation_File_Form
        form = Add_Pronunciation_File_Form(request.POST)

        if form.is_valid(uploaded_file):
            language_code = pronunciation.language.code.lower()
            filename = self.get_filename(language_code,
                                        pronunciation.text,
                                        form.data["source"],
                                        form.data["accent"])
            path = self.get_file_local_path(language_code,
                                            filename)
            with open(path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
            pronunciation_file = form.save(pronunciation, filename)
            print(request.POST.get('choose'), form.data)
            if request.POST.get('choose'):
                pronunciation_file.choose()
            return redirect(pronunciation.get_absolute_url())
        else:
            return self.return_adding_form(request, form, pronunciation)

    @classmethod
    def return_adding_form(self, request, form, pronunciation):
        return render(request,
                    os.path.join(self.template_dir, "add_pronunciation_file_template.html"),
                    {"form": form,
                    "pronunciation": pronunciation,
                    "title": "Adding pronunciation file for"})

    def choose(self):
        self.choosen = True
        self.save()
        self.unselect_other_choosen()

    def unselect_other_choosen(self):
        other_pronunciation_files = self.__class__.objects.filter(pronunciation=self.pronunciation,
                                                                choosen=True).exclude(id=self.id)
        other_pronunciation_files.update(choosen=False)

    @classmethod
    def get_pronunciation_files(self, pronunciation):
        return self.objects.filter(pronunciation=pronunciation)

    @classmethod
    def get_choosen_pronunciation_file(self, pronunciation):
        pronunciation_files_basic_queryset = self.get_pronunciation_files(pronunciation)
        pronunciation_files = pronunciation_files_basic_queryset.filter(choosen=True)
        
        if pronunciation_files.count() == 1:
            pronunciation_file = pronunciation_files[0]
        elif pronunciation_files.count() > 1: # if there are extra pronunciation_files
            pronunciation_files = pronunciation_files.order_by("-created_at")
            pronunciation_file = pronunciation_files[0]
            pronunciation_file.unselect_other_choosen()
        elif pronunciation_files_basic_queryset.count() > 0: # no choosen pronunciation files
            pronunciation_files = pronunciation_files.order_by("-created_at")
            pronunciation_file = pronunciation_files_basic_queryset[0]
            pronunciation_file.choosen = True
            pronunciation_file.save()
        else: # no pronunciation files
            pronunciation_file = pronunciation.create_pronunciation_file()
        return pronunciation_file

    @classmethod
    def get_random_pronunciation_file(self, pronunciation):
        pronunciation_files_basic_queryset = self.get_pronunciation_files(pronunciation)
        random_index = randint(0, pronunciation_files_basic_queryset.count() - 1)
        return pronunciation_files_basic_queryset[random_index]

    def delete(self, return_pronunciation_url=True, delete_file=True):
        if delete_file:
            filepath = self.get_filepath()
            os.remove(filepath)
            print(self, filepath)
        if return_pronunciation_url:
            pronunciation_files_count = self.pronunciation.get_pronunciation_files_queryset().count()
            if pronunciation_files_count > 1:
                returned_url = self.pronunciation.get_absolute_url()
            else:
                returned_url = reverse("pronunciations_files_list")
        else:
            returned_url = None
        super().delete()
        return returned_url

    @classmethod
    def search(self, searching_param_value):
        return self.objects.search(searching_param_value)