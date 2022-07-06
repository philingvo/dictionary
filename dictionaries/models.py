from datetime import datetime
import json
import os
import mimetypes
import re
from urllib.parse import quote
from wsgiref.util import FileWrapper
from django.db import models
from django.urls import reverse
from django.conf import settings
from django.utils.translation import activate, get_language_info, gettext_noop
from dictionary.settings import undefined_language_name, undefined_language_code, default_defined_langauge_code
from django.utils import timezone
from django.http import HttpResponse


def languages_list():
	languages_list = settings.LANGUAGES
	languages_list.append((undefined_language_code, gettext_noop(undefined_language_name)))
	return languages_list

class List_Model(models.Model):

	change_position_url = None
	container_field_name = None
	content_field_name = None
	container_container_model = None

	class Meta:
		abstract = True

	def __str__(self):
		return self.__getattribute__(self.content_field_name).__str__()

	def container_description(self):
		return self.__getattribute__(self.container_field_name).__str__()

	def get_change_position_up_url(self):
		return self.get_change_position_url('up')

	def get_change_position_down_url(self):
		return self.get_change_position_url('down')

	def get_model(self, field_name):
		return self.__getattribute__(self, field_name).field.related_model

	def get_details_url(self):
		return self.__getattribute__(self.content_field_name).get_absolute_url()

	def get_container_details_url(self):
		return self.__getattribute__(self.container_field_name).get_absolute_url()

	def get_content_list_url(self):
		return self.__getattribute__(self.content_field_name).get_content_list_url()

	def get_container_content_list_url(self):
		return self.__getattribute__(self.container_field_name).get_content_list_url()

	def color(self):
		return self.__getattribute__(self.content_field_name).color

	def get_container_title(self):
		return self.container.id

	def get_content_item(self):
		return self.__getattribute__(self.content_field_name)

	def get_item_id(self):
		return self.get_content_item().id

	@property
	def is_storage(self):
		return self.get_content_item().storage

	@classmethod
	def change_position(self, *args, **kwargs):
		item = self.change_item_position(*args, **kwargs)
		return item.get_list_url()

	@classmethod
	def change_item_position(self, *args, **kwargs):
		container = kwargs.get('container')
		position = kwargs['position']
		direction = kwargs['direction']
		internal = kwargs.get('internal')

		items = self.get_items(container)
		item = items.get(position=position)

		new_position = False
		total_items = items.count()
		if direction == 'up':
			if position > 1:
				new_position = position - 1
		elif direction == 'down':
			if position > 0 and position < total_items:
				new_position = position + 1
		elif direction == 'end':
			if position > 0 and position < total_items:
				new_position = total_items
		elif direction == 'zero' and internal:
			new_position = 0
		else:
			if direction.isdigit():
				new_position = int(direction)
				if new_position < 1 or new_position > total_items or new_position == position:
					new_position = False
				elif position < new_position:
					new_position -= 1

		if new_position:
			if position < new_position:
				items_range = items.filter(position__gte=position, position__lte=new_position).order_by("position")
				current_item = items_range[0]
				last_item = items_range[items_range.count() - 1]
				current_item.position = last_item.position

				items_to_update = [current_item]

				for item_in_range in items_range[1:]:
					item_in_range.position -= 1
					items_to_update.append(item_in_range)
				self.objects.bulk_update(items_to_update, ['position'])

			elif position > new_position and new_position != 0:
				items_range = items.filter(position__gte=new_position, position__lte=position).order_by("position")
				current_item = items_range[items_range.count() - 1]
				first_item = items_range[0]
				current_item.position = first_item.position
				items_to_update = [current_item]
				
				for item_in_range in items_range[:items_range.count()-1]:
					item_in_range.position += 1
					items_to_update.append(item_in_range)
				self.objects.bulk_update(items_to_update, ['position'])

			elif position > new_position and new_position == 0:
				items_range = items.filter(position__gte=new_position)
				zero_item = items_range[0]
				zero_item.position = 0
				items_to_update = [zero_item]
				for greater_item in items_range[1:]:
					greater_item.position -= 1
					items_to_update.append(item_in_range)

				self.objects.bulk_update(items_to_update, ['position'])

			returning_item = current_item
		else:
			returning_item = item

		return returning_item

	@classmethod
	def delete_item(self, *args, **kwargs):
		item_in_list_id = kwargs['pk']
		item_in_list = self.objects.get(pk=item_in_list_id)

		greater_items_filter_dict = {'position__gt': item_in_list.position}
		if item_in_list.container_field_name:
			greater_items_filter_dict[item_in_list.container_field_name] = item_in_list.container.id
		else:
			if 'storage' in greater_items_filter_dict:
				greater_items_filter_dict['storage'] = item_in_list.storage # FOR SUBJECT

		back_redirect_url = item_in_list.delete()
		lower_items = self.objects.filter(**greater_items_filter_dict)
		if lower_items.count() > 0:
			for lower_item in lower_items:
				lower_item.position -= 1
				lower_item.save()

		return back_redirect_url

	@classmethod
	def insert_item(self, *args, **kwargs):
		container_id = kwargs["pk"]
		to_delete = kwargs['to_delete']
		content_items_ids_to_insert = kwargs['content_items_ids_to_insert']

		if 'source_container_model' in kwargs:
			source_container_model = kwargs['source_container_model']
		else:
			source_container_model = self
		content_items_to_insert = source_container_model.objects.filter(**{"id__in": content_items_ids_to_insert}).order_by('position')
		container_model = self.get_container_model()
		container = container_model.objects.get(id=container_id)
		items_in_container = self.objects.filter(**{self.container_field_name: container_id}).count()
		
		for content_item in content_items_to_insert:
			items_in_container += 1
			item = self(**{self.container_field_name: container,
							self.content_field_name: content_item.__getattribute__(self.content_field_name),
							'position': items_in_container})
			item.save()
			if to_delete:
				self.delete_item(pk=content_item.id)
		return container.get_content_list_url()

	@classmethod
	def get_container_model(self):
		return self.get_model(self, self.container_field_name)

	@classmethod
	def get_content_model(self):
		return self.get_model(self, self.content_field_name)

	@property
	def container(self):
		if self.container_field_name:
			return self.__getattribute__(self.container_field_name)
		else:
			return False

	def get_change_position_url(self, direction):
		return reverse(self.change_position_url, kwargs={'container': self.get_container_title(),
														'position': self.position,
														'direction': direction})

	def get_list_url(self):
		return self.get_absolute_url()

	@classmethod
	def get_items(self, container):		
		return self.objects.filter(**{self.container_field_name: container})		

class Item_Model(models.Model):

	text_abstract = "abstract"

	class Meta:
		abstract = True

	@classmethod
	def save_color(self, id, color):
		# https://www.rapidtables.com/web/color/RGB_Color.html
		model_name = self.__name__.lower()
		objects = self.objects.filter(id=id)
		objects_count = objects.count()
		if objects_count > 1:
			response_text = "There are more than one {} with this ID".format(model_name)
		elif objects_count < 1:
			response_text = "There is no {} with this ID".format(model_name)
		else:
			object = objects[0]
			colors_list = ('white', 'red', 'crimson', 'orange', 'gold', 'lime', 'blue', 'yellow', 'cyan', 'magenta', 'silver', 'gray', 'maroon', 'olive', 'green',	'purple', 'teal')
			if color in colors_list:
				object.color = color
				object.save()
				response_text = "Color for {} has been changed".format(model_name)
			elif color == None:
				object.color = color
				object.save()
				response_text = "Color for {} has been deleted".format(model_name)
			else:
				response_text = "Wrong color name"
		return response_text

	@classmethod		
	def save_text_abstract(self, id, text):
		model_name = self.__name__
		objects = self.objects.filter(id=id)
		objects_count = objects.count()
		if objects_count > 1:
			response_text = "There are more than one {} with this ID".format(model_name.lower)
		elif objects_count < 1:
			response_text = "There is no {} with this ID".format(model_name.lower)
		else:
			object = objects[0]
			if text == '':
				text = None
			if 'abstract' in object.__dict__:
				object.abstract = text
			else:
				object.comment = text
			object.save()
			if text:
				response_text = "{}'s {} has been saved".format(model_name, self.text_abstract)
			else:
				response_text = "{}'s {} has been deleted".format(model_name, self.text_abstract)
		return response_text

	@staticmethod
	def prepare_text(text, prepare_for_url=True):
		prepared_text = re.sub("[/\\:*«<>#&?\n\r\t]", " ", text)
		return quote(prepared_text)

	def get_pronounce_queryset(self, text, lang):
		return "?text={}&lang={}".format(text, lang)

	def get_pronunce_url(self, text, lang):
		text = self.prepare_text(text)
		return reverse('pronounce') + self.get_pronounce_queryset(text, lang)

class Language(models.Model):

	original_name = models.CharField(max_length=255)
	english_name = models.CharField(max_length=9, choices=languages_list())
	translation_name = models.CharField(max_length=255, null=True, blank=True)
	code = models.CharField(max_length=9, null=True, blank=True)
	default = models.BooleanField(default=False)

	undefined_language_name = undefined_language_name
	undefined_language_code = undefined_language_code
	default_defined_langauge_code = default_defined_langauge_code
	add_new_item_pathname = 'add_new_language'
	list_namepath = 'languages'

	def __str__(self):
		if self.code != self.undefined_language_code:
			code_name = '{}: '.format(self.code.upper())
		else:
			code_name = ''
		if self.translation_name:
			translation = self.translation_name
		elif self.code != self.undefined_language_code:
			translation = get_language_info(self.english_name)
		else:
			translation = False
		name = code_name + self.original_name.capitalize()
		if translation:
			name = '{} - {}'.format(name, translation.capitalize())
		return name

	def get_absolute_url(self):
		return reverse('update_language', kwargs={'pk': self.id})

	def get_list_url(self):
		return reverse('languages')

	def get_delete_url(self):
		return reverse('delete_language', kwargs={'pk': self.id})

	@classmethod
	def get_add_new_item_into_end_url(self):
		return reverse(self.add_new_item_pathname)

	@classmethod
	def ensure_languages_existence(self):
		if self.objects.all().count() == 0:
			self.get_default_language()

	@classmethod
	def get_default_language(self):

		def create_default_language():
			default_language = self(original_name=self.undefined_language_name,
									english_name=self.undefined_language_name,
									code=self.undefined_language_code,
									default=True)
			default_language.save()
			return default_language

		def assign_default_defined_code_for_languages(queryset):
			for language in queryset:
				language.code = self.default_defined_langauge_code
				language.save()

		default_languages = self.objects.filter(default=True)
		default_languages_count = default_languages.count()
		
		if default_languages_count == 1: # Default language has been created already
			return default_languages[0]
		
		elif default_languages_count < 1: # Default language hasn't been created yet
			all_languages = self.objects.all()
			
			if all_languages.count() == 0: # No one language has been created yet - Create default language
				return create_default_language()
			
			else: # There are some languages already
				all_languages_without_code = all_languages.filter(code=None)
				all_languages_without_code_count = all_languages_without_code.count()
				
				if all_languages_without_code_count == 1: # Get language without code and make it as the default language
					default_language = all_languages_without_code[0]
					default_language.default = True
					default_language.save()
					return default_language

				elif all_languages_without_code_count < 1: # Create default language
					return create_default_language()
				
				elif all_languages_without_code_count > 1: # There are more than one language without code
					all_languages_with_undefined_language_name = all_languages_without_code.filter(english_name=self.undefined_language_name)
					all_languages_with_undefined_language_name_count = all_languages_with_undefined_language_name.count()
					
					if all_languages_with_undefined_language_name_count == 1: # Get language without code and with undefined language name and make it as the default language
						default_language = all_languages_with_undefined_language_name[0]
						default_language.default = True
						default_language.code = None
						default_language.save()
						assign_default_defined_code_for_languages(all_languages_without_code.exclude(default=True))
						return default_language
					
					elif all_languages_with_undefined_language_name_count < 1: # Create default language						
						assign_default_defined_code_for_languages(all_languages_without_code)
						return create_default_language()
					
					elif all_languages_with_undefined_language_name_count > 1: # There are more than one language with undefined language name
						default_language = all_languages_with_undefined_language_name.order_by('id')[0]
						default_language.default = True
						default_language.save()
						
						increment = 0
						for language in all_languages_without_code.exclude(default=True):
							increment += 1
							language.english_name += ' {}'.format(increment)
							language.save()
						return default_language

	@staticmethod
	def get_language_info(english_name):
		activate(User.get_user_language())
		return get_language_info(english_name)

	@classmethod
	def insert_default_languages_names(self, form):
		if form.instance.english_name == self.undefined_language_code:
			if not form.instance.original_name:
				form.instance.original_name = self.undefined_language_name
		else:
			language_info = self.get_language_info(form.instance.english_name)
			if not form.instance.original_name:
				form.instance.original_name = language_info['name_local'].lower()
			if not form.instance.translation_name:
				form.instance.translation_name = language_info['name_translated'].lower()

	@classmethod
	def language_with_english_name_exisits(self, name):
		return self.objects.filter(english_name=name).count() > 0

	def delete(self):

		def change_language(queryset, default_language):
			for item in queryset:
				item.language = default_language
				item.save()

		default_language = self.__class__.get_default_language()
		for model in [Subject, Topic, Set_Type, Part_Type]:
			queryset = model.objects.filter(language=self)
			change_language(queryset, default_language)
		super().delete()
		return self.get_list_url()

	@classmethod
	def find_or_create_language(self, language_code):
		language_code = language_code.lower()
		languages = self.objects.filter(code=language_code)
		if languages.count() > 0:
			return languages[0]
		else:
			for language_tuple in languages_list():
				if language_tuple[0] == language_code:
					language_info = self.get_language_info(language_tuple[0])
					language = self(code=language_code,
									english_name=language_code,
									original_name = language_info['name_local'].lower(),
									translation_name = language_info['name_translated'].lower())
					language.save()
					return language
			return self.get_default_language()

class Subject(List_Model, Item_Model):

	position = models.IntegerField(null=False)
	title = models.CharField(max_length=255)
	abstract = models.TextField(blank=True, null=True)
	language = models.ForeignKey(Language, models.PROTECT)
	storage = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)
	color = models.CharField(max_length=255, null=True)

	change_position_url = 'change_subject_position'
	add_new_item_pathname = 'add_new_subject'
	storage_title = 'Topics without subjects'
	list_namepath = 'show_subjects'
	storage_list_namepath = 'show_storage_subjects'

	def __str__(self):
		if self.language.code:
			return '({}) {}'.format(self.language.code.upper(), self.title)
		else:
			return self.title

	def get_absolute_url(self):
		return reverse('show_subject', kwargs={'pk': self.id})

	def get_details_url(self):
		return self.get_absolute_url()

	def get_delete_url(self):
		return reverse('delete_subject', kwargs={'pk': self.id})

	def get_content_list_url(self):
		return reverse('show_subject_topics', kwargs={'subject': self.id})

	def get_list_url(self):
		return self.define_list_url(self.storage)

	def get_insert_content_item_into_container_url(self):
		return reverse('insert_topic_into_subject', kwargs={'pk': self.pk})

	def get_activate_url(self):
		return reverse('activate_subject', kwargs={'pk': self.pk})

	def get_container_title(self):
		return self.define_subject_type(self.storage)

	def get_item_id(self):
		return self.id

	@property
	def is_storage(self):
		return self.storage

	@classmethod
	def get_active_subjects(self):
		return self.objects.filter(storage=False)

	@classmethod
	def get_storage_subjects(self):
		return self.objects.filter(storage=True)

	@classmethod
	def define_list_url(self, storage):
		return reverse(self.storage_list_namepath if storage else self.list_namepath)

	@staticmethod
	def define_subject_type(storage):
		return 'storage' if storage else 'active'

	@staticmethod
	def define_storage(subject_type):
		return  True if subject_type == 'storage' else False
	
	@classmethod
	def get_add_new_item_into_end_url(self, storage=False):
		return reverse(self.add_new_item_pathname, kwargs={'container': self.define_subject_type(storage),
															'direction': 'end'})

	@classmethod
	def get_items(self, subject_type='active'):
		return self.objects.filter(storage=self.define_storage(subject_type))

	def delete(self):
		if self.storage:
			back_redirect_url = self.get_list_url()
			subject_for_topics = self.__class__.get_storage_subject_for_topics_without_subjects()
			if self != subject_for_topics: # Deleting subject for topics is forbiden
				topics_in_subject = Topics.objects.filter(subject=self)
				for topic in topics_in_subject:
					topic.delete() # Move all topics out this storage to storage subjecs for topics					
				super().delete() # Delete subject
		else: # move this subject to storage subjects
			back_redirect_url = self.get_list_url()
			self.storage = True
			storages_count = self.__class__.objects.filter(storage=True).exclude(position=0).count()
			self.position = storages_count + 1
			self.save()
		return back_redirect_url

	@classmethod
	def get_storage_subject_for_topics_without_subjects(self):
	# This method hasn't checked and refactored yet!

		def create_subject_for_topics():
			storage_subject_for_topic = self(title=self.storage_title,
											storage=True,
											position=0,
											language=Language.get_default_language())
			storage_subject_for_topic.save()
			return storage_subject_for_topic

		def change_subject_title_function(storage_subject):
			storage_subject.title += ' {}'.format(datetime.now())

		def assign_non_zero_positions(queryset, change_subject_title=False):
			storage_subjects_count = self.objects.filter(storage=True).count()
			for storage_subject in queryset:
				storage_subject.position = storage_subjects_count + 1
				if change_subject_title:
					change_subject_title_function(storage_subject)
				storage_subject.save()

		storage_subjects_for_topics = self.objects.filter(storage=True, position=0)
		storage_subjects_for_topic_count = storage_subjects_for_topics.count()
		if storage_subjects_for_topic_count == 1: # storage_subjects_for_topic has been created
			return storage_subjects_for_topics[0]
		
		elif storage_subjects_for_topic_count < 1: # storage_subjects_for_topic hasn't been created
			storage_subjects = self.objects.filter(storage=True)
			storage_subjects_count = storage_subjects.count()
			if storage_subjects_count > 0: # There are some storage subjects
				storage_subjects_with_title = storage_subjects.filter(title=self.storage_title).order_by('created_at')
				storage_subjects_with_title_count = storage_subjects_with_title.count()
				if storage_subjects_with_title_count < 1: # There is no storage subjects with title. Create storage subject
					return create_subject_for_topics()
				else: # There are more than one storage subjects with title
					storage_subject_for_topics = storage_subjects_with_title[0]
					self.change_position(container='storage',
										position=storage_subject_for_topics.position,
										direction='zero',
										internal=True)
					for storage_subject in storage_subjects_with_title.filter(position=0):
						change_subject_title_function(storage_subject)
					return self.objects.get(storage=True, position=0)
			else: # There is no one storage subject
				return create_subject_for_topics()
		
		elif storage_subjects_for_topic_count > 1: # There are more than one storage subject with zero position
			storage_subjects_for_topics_with_title = storage_subjects_for_topics.filter(title=self.storage_title).order_by('created_at')
			storage_subjects_for_topics_with_title_count = storage_subjects_for_topics_with_title.count()
			
			if storage_subjects_for_topics_with_title_count == 1: # There one storage subject with title
				assign_non_zero_positions(storage_subjects_for_topics.exclude(title=self.storage_title))				
				return storage_subjects_for_topics_with_title[0]
			
			elif storage_subjects_for_topics_with_title_count < 1: # There no one storage subject with title. Create it
				assign_non_zero_positions(storage_subjects_for_topics)
				return create_subject_for_topics()

			elif storage_subjects_for_topics_with_title_count > 1: # There more than one storage subjects with title
				assign_non_zero_positions(storage_subjects_for_topics_with_title[1:], True)
				return storage_subjects_for_topics_with_title[0]

	@classmethod
	def activate(self, id):
		storage_subject = self.objects.get(id=id)
		storage_subject.storage = False
		active_subjects = self.get_items()
		storage_subject.position = active_subjects.count() + 1
		storage_subject.save()
		return storage_subject.get_list_url()

class Topic(Item_Model):

	title = models.CharField(max_length=255)
	abstract = models.TextField(blank=True, null=True)
	language = models.ForeignKey(Language, models.PROTECT)
	storage = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)
	color = models.CharField(max_length=255, null=True)

	storage_title = 'Sets without topics'

	def __str__(self):
		if self.language.code:
			return '({}) {}'.format(self.language.code.upper(), self.title)
		else:
			return self.title

	def get_absolute_url(self):
		return reverse('show_topic', kwargs={'pk': self.id})

	def get_content_list_url(self):
		return reverse('show_topic_sets', kwargs={'topic': self.id})

	def get_containers_list_url(self):
		return reverse('show_topic_subjects', kwargs={'pk': self.id})

	def get_insert_content_item_into_container_url(self):
		return reverse('insert_set_into_topic', kwargs={'pk': self.pk})

	@classmethod
	def get_storage_topic_for_sets_without_topic(self):
		# This method hasn't checked and refactored yet!

		def create_topic_for_sets(subject_for_topics_id):
			storage_topic = self(title=self.storage_title,
								language=Language.get_default_language(),
								storage=True)
			storage_topic.save()
			storage_topic_in_subject = Topics(topic=storage_topic,
											subject_id=subject_for_topics_id,
											position=0)
			storage_topic_in_subject.save()
			return storage_topic

		def change_topic_position(storage_subject_id, topic_position):
			Topics.change_position(container=storage_subject_id,
									position=topic_position,
									direction='zero',
									internal=True)
			return Topics.get(topic__storage=True, subject__id=storage_subject_id, position=0).topic

		def insert_topic_to_storage_subject(storage_subject_id, topic_id):
			Subject.insert_item(pk=storage_subject_id, 
								to_delete=True,
								content_items_ids_to_insert=[topic_id])
			return Topics.get(topic__storage=True, subject=subject_for_topics)

		def make_topic_as_storage_insert_to_storage_subject_change_position_to_zero(topic, storage_subject_id):
			container_topic = topic.topic
			container_topic.storage = True
			container_topic.save()
			# Move this storage topic to the storage subject
			topic = insert_topic_to_storage_subject(subject_for_topics.id, topic)
			# Change this storage topic position to zero
			return change_topic_position(storage_subject_id, topic.position)

		def change_title_function(container_topic, increment):
			container_topic = topic.topic
			container_topic.title += ' {}'.format(increment)
			container_topic.save()

		def make_topic_as_non_storage_function(topic):
			container_topic = topic.topic
			container_topic.storage = False
			container_topic.save()

		def change_topics_props(queryset, change_title=False, make_topic_as_non_storage=False):
			increment = 0
			for topic in queryset:
				if change_title:
					increment += 1
					change_title_function(topic.topic, increment)
				if make_topic_as_non_storage:
					make_topic_as_non_storage_function(topic)
				topic.save()

		def change_topics_positions(queryset, change_title=False):
			non_zero_topics_in_storage_topic_count = Topics.objects.filter(subject=subject_for_topics).exclude(position=0).count()
			increment = 0
			for storage_topic in queryset:
				non_zero_topics_in_storage_topic_count += 1
				storage_topic.position = non_zero_topics_in_storage_topic_count
				make_topic_as_non_storage_function(storage_topic)
				if change_title:
					increment += 1
					change_title_function(storage_topic, increment)				
				storage_topic.save()

		subject_for_topics = Subject.get_storage_subject_for_topics_without_subjects()
		storage_topics = Topics.objects.filter(topic__storage=True, subject=subject_for_topics, position=0)
		storage_topics_count = storage_topics.count()
		
		if storage_topics_count == 1: # The storage topic for sets without topics has been created
			return storage_topics[0].topic
		
		elif storage_topics_count < 1: # The storage topic for sets without topics has been found. Try to find non zero positions
			storage_topics_with_non_zero_positions = Topics.objects.filter(topic__storage=True, subject=subject_for_topics)
			storage_topics_with_non_zero_positions_count = storage_topics_with_non_zero_positions.count()
			
			if storage_topics_with_non_zero_positions_count == 1: # Found one storage topic in the storage subject. Change position to zero
				return change_topic_position(subject_for_topics.id,
											storage_topics_with_non_zero_positions[0].position)
			
			elif storage_topics_with_non_zero_positions_count < 1: # No storage topics have been found. Try to find a simple storage topic
				storage_topics_with_non_zero_positions_out_storage_subject = storage_topics_with_non_zero_positions.exclude(subject=subject_for_topics)
				storage_topics_with_non_zero_positions_out_storage_subject_count = storage_topics_with_non_zero_positions_out_storage_subject.count()
				
				if storage_topics_with_non_zero_positions_out_storage_subject_count == 1: # Find one simple storage topic
					# Move this storage topic to the storage subject
					topic = insert_topic_to_storage_subject(subject_for_topics.id, storage_topics_with_non_zero_positions_out_storage_subject[0].id)
					# Change this storage topic position to zero
					return change_topic_position(subject_for_topics.id,	topic.position)
				
				elif storage_topics_with_non_zero_positions_out_storage_subject_count < 1: # There is no one storage topic
					non_storage_topics_with_non_zero_positions_out_storage_subject_with_title = storage_topics_with_non_zero_positions_out_storage_subject.filter(topic__title=self.storage_title).order_by("topic__created_at")
					non_storage_topics_with_non_zero_positions_out_storage_subject_with_title_count = non_storage_topics_with_non_zero_positions_out_storage_subject_with_title.count()
					
					if non_storage_topics_with_non_zero_positions_out_storage_subject_with_title_count == 1: # Find one topic with proper title
						return make_topic_as_storage_insert_to_storage_subject_change_position_to_zero(non_storage_topics_with_non_zero_positions_out_storage_subject_with_title[0], subject_for_topics.id)
					
					elif non_storage_topics_with_non_zero_positions_out_storage_subject_with_title_count < 1:
						return create_topic_for_sets(subject_for_topics.id)
					
					elif non_storage_topics_with_non_zero_positions_out_storage_subject_with_title_count > 1:
						topic = make_topic_as_storage_insert_to_storage_subject_change_position_to_zero(non_storage_topics_with_non_zero_positions_out_storage_subject_with_title[0], subject_for_topics.id)
						non_storage_topics_with_non_zero_positions_out_storage_subject_with_title = non_storage_topics_with_non_zero_positions_out_storage_subject_with_title.exclude(position=0)
						change_topics_props(non_storage_topics_with_non_zero_positions_out_storage_subject_with_title, change_title=True)
						return topic				
				
				elif storage_topics_with_non_zero_positions_out_storage_subject_count > 1: # There are more than one storage topics
					storage_topics_with_non_zero_positions_out_storage_subject_with_title = storage_topics_with_non_zero_positions_out_storage_subject.filter(topic__title=self.storage_title).order_by("topic__created_at")
					storage_topics_with_non_zero_positions_out_storage_subject_with_title_count = storage_topics_with_non_zero_positions_out_storage_subject_with_title.count()
					
					if storage_topics_with_non_zero_positions_out_storage_subject_with_title_count == 1:
						topic = insert_topic_to_storage_subject(subject_for_topics.id, storage_topics_with_non_zero_positions_out_storage_subject_with_title[0].id)
						topic = change_topic_position(subject_for_topics.id, topic.position)
						storage_topics_with_non_zero_positions_out_storage_subject_with_title = storage_topics_with_non_zero_positions_out_storage_subject_with_title.exclude(position=0)
						change_topics_props(storage_topics_with_non_zero_positions_out_storage_subject_with_title, make_topic_as_non_storage=True)
						return topic

					elif storage_topics_with_non_zero_positions_out_storage_subject_with_title_count < 1:
						change_topics_props(storage_topics_with_non_zero_positions_out_storage_subject_with_title, True)
						return create_topic_for_sets(subject_for_topics.id)

					elif storage_topics_with_non_zero_positions_out_storage_subject_with_title_count > 1:
						topic = insert_topic_to_storage_subject(subject_for_topics.id, storage_topics_with_non_zero_positions_out_storage_subject_with_title[0].id)
						topic = change_topic_position(subject_for_topics.id, topic.position)
						storage_topics_with_non_zero_positions_out_storage_subject_with_title = storage_topics_with_non_zero_positions_out_storage_subject_with_title.exclude(position=0)
						change_topics_props(storage_topics_with_non_zero_positions_out_storage_subject_with_title, change_title=True, make_topic_as_non_storage=True)
						return topic
		
		elif storage_topics_count > 1: # There are too many storage topics. Try to find proper one
			storage_topics_with_title = storage_topics.filter(topic__title=self.storage_title).order_by("topic__created_at")
			storage_topics_with_title_count = storage_topics_with_title.count()
			
			if storage_topics_with_title_count == 1: # There is one storage topic with title				
				change_topics_positions(storage_topics_with_title[1:])
				return storage_topics_with_title[0].topic

			elif storage_topics_with_title_count < 1: # There is no storage topic with title
				change_topics_positions(storage_topics_with_title)
				return create_topic_for_sets(subject_for_topics.id)
			
			elif storage_topics_with_title_count > 1: # There are more then one storage topic with title
				change_topics_positions(storage_topics_with_title[1:], change_title=True)
				return storage_topics_with_title[0].topic

class Topics(List_Model):

	position = models.IntegerField(null=False)
	subject = models.ForeignKey(Subject, models.PROTECT)
	topic = models.ForeignKey(Topic, models.PROTECT)

	container_field_name = 'subject'
	content_field_name = 'topic'
	change_position_url = 'change_topics_position'
	add_new_item_pathname = 'add_new_topic_into_subject'

	def get_absolute_url(self):
		return reverse('show_subject_topics', kwargs={'subject': self.subject.id})

	def get_delete_url(self):
		return reverse('delete_subject_topic', kwargs={'pk': self.id})

	def get_add_new_item_into_end_url(self):
		return reverse(self.add_new_item_pathname, kwargs={'container': self.subject.id,
														'direction': 'end'})

	def set_container(self, container_object):
		self.subject = container_object

	def set_content(self, content_object):
		self.topic = content_object

	def delete(self):
		back_redirect_url = self.container.get_content_list_url()
		topic_in_other_subjects = self.__class__.objects.filter(topic=self.topic.id)
		topic_in_other_subjects_count = topic_in_other_subjects.count()
		if topic_in_other_subjects_count > 1: # Other subjects contain this topic excluding this subject
			super().delete() # Delete topic in subject
		else: # Only this subject contains this topic
			storage_subject_for_topics = Subject.get_storage_subject_for_topics_without_subjects()
			if self.subject == storage_subject_for_topics:
				sets_in_topic = Sets.objects.filter(topic=self.topic)
				for set in sets_in_topic:
					set.delete() # Remove or delete set
				super().delete() # Delete topic in subject
				self.topic.delete() # Delete topic
			else: # Move this topic to the storage subject for topics without subjects
				Topics.insert_item(pk=storage_subject_for_topics.id,
									to_delete=False,
									content_items_ids_to_insert=[self.id])
				super().delete() # Delete topic in subject

		return back_redirect_url

class Set_Type(models.Model):

	name = models.CharField(max_length=255)
	abstract = models.TextField(blank=True, null=True)
	language = models.ForeignKey(Language, models.PROTECT)

	add_new_item_pathname = 'add_new_set_type'
	list_namepath = 'sets_types'

	def __str__(self):
		if self.language.code:
			language = '({}) '.format(self.language.code.upper())
		else:
			language = ''
		return '{}{}'.format(language, self.name)

	def get_absolute_url(self):
		return reverse('update_set_type', kwargs={'pk': self.id})

	def get_delete_url(self):
		return reverse('delete_set_types', kwargs={'pk': self.id})

	def get_content_list_url(self):
		return self.get_absolute_url()

	def get_list_url(self):
		return reverse(self.list_namepath)

	def get_containers_list_url(self):
		return reverse('show_sets_for_set_types', kwargs={'pk': self.id})

	def get_add_part_type_in_set_type_url(self):
		return Parts_Types.get_add_new_item_into_end_url(self)

	@classmethod
	def get_add_new_item_into_end_url(self):
		return reverse(self.add_new_item_pathname)

	def parts_types(self):
		return Parts_Types.objects.filter(set_type=self).order_by('position')

	@property
	def sets_exist(self):
		set_for_set_type = Set.objects.filter(type=self)
		return set_for_set_type.count() > 0

	@property
	def ready_to_delete(self):
		return not self.sets_exist and self.parts_types.count() < 1

	def delete(self):
		# Set type's deleting is not possible when there are sets with this set types.
		# If you really want to delete a set type, delete sets with this set type first!'
		if self.ready_to_delete:
			parts_types = Parts_Types.objects.filter(set_type=self)
			for part_type in parts_types:
				part_type.delete()
			super().delete()
		return self.get_list_url()

	@classmethod
	def get_undefined_set_type_name(self):
		return 'Undefined set type at {}'.format(datetime.now())

	@classmethod
	def create_undefined_set_type(self):
		set_type = self(name=self.get_undefined_set_type_name(),
						abstract=None,
						language=Language.get_default_language())
		set_type.save()
		return set_type

	@classmethod
	def get_imported_set_type(self, imported_set):

		def check_parts_types_existance(set_information):
			parts_types = set_information.get("parts_types")
			if parts_types and isinstance(parts_types, list) and len(parts_types) > 0:
				for part_type in parts_types:
					if not ("position" in part_type and "type" in part_type):
						return False
				return True
			else:
				return False

		def check_set_type_appropiance(set_type, set_information):
			parts_types = set_information.get("parts_types")
			return Parts_Types.check_imported_parts_types(set_type, parts_types)

		def find_proper_set_type(set_types, set_information):
			for set_type in set_types:
				if check_set_type_appropiance(set_type, set_information):
					return set_type

		def find_or_create_proper_set_type(set_information):
			set_type = find_proper_set_type(self.objects.all(), set_information)
			if set_type:
				return set_type
			else:
				return create_imported_set_type(set_information)

		def create_imported_set_type_using_only_parts_types(set_information):
			set_type = self.create_undefined_set_type()
			put_parts_types_for_set_type(set_type, set_information)
			return set_type

		def create_imported_set_type(set_information):
			set_properties = set_information["set_properties"]
			set_type_properties = set_properties.get("type")

			if set_type_properties:
				language = set_type_properties.get("language")
				if language and 'code' in language:
					language_code = language["code"]
				else:
					language_code = ''
				language = Language.find_or_create_language(language_code)

				name = set_type_properties.get("name")
				if not name:
					name = self.get_undefined_set_type_name()

				abstract = set_type_properties.get("abstract")
				if not abstract:
					abstract = None
			
				set_type = self(name=name,
								abstract=abstract,
								language=language)
				set_type.save()
			else:
				set_type = self.create_undefined_set_type()

			put_parts_types_for_set_type(set_type, set_information)
			return set_type

		def put_parts_types_for_set_type(set_type, set_information):
			parts_types = set_information.get("parts_types")
			for part_type_properties in set_information["parts_types"]:
				part_type = Part_Type.find_or_create_part_type(part_type_properties['type'])
				part_type_for_set_type = Parts_Types(set_type=set_type,
													type=part_type,
													position=part_type_properties["position"],
													main_color=part_type_properties["main_color"],
													background_color=part_type_properties["background_color"])
				part_type_for_set_type.save()

		set_information = imported_set.get("set")
		if set_information:
			if check_parts_types_existance(set_information):
				set_properties = set_information.get("set_properties")
				
				if set_properties:
					set_type = set_properties.get("type")

					if set_type and "name" in set_type:
						set_type_name = set_type["name"]
						set_types = self.objects.filter(name=set_type_name)
						set_types_count = set_types.count()
						
						if set_types_count > 1:
							set_type = find_proper_set_type(set_types, set_information)
							if set_type:
								return set_type
							else:
								return find_or_create_proper_set_type(set_information)
						
						elif set_types_count == 1:
							set_type = set_types[0]
							if check_set_type_appropiance(set_type, set_information):
								return set_type
							else:
								return find_or_create_proper_set_type(set_information)
						
						elif set_types_count < 1:
							return find_or_create_proper_set_type(set_information)
					else:
						return find_or_create_proper_set_type(set_information)
				else:
					return create_imported_set_type_using_only_parts_types(set_information) # USE ONLY PARTS' TYPES
			else:
				return False # No part types
		else:
			return False # No set infortation

class Part_Format(models.Model):

	name = models.CharField(max_length=255)
	possible_parts_formats_names = ['text', 'url']

	def __str__(self):
		return self.name

	@classmethod
	def ensure_part_formats_existence(self):
		if self.objects.all().count() < len(self.possible_parts_formats_names):
			self.create_text_format()

	@classmethod
	def create_text_format(self):
		for format_name in self.possible_parts_formats_names:
			if self.objects.filter(name=format_name).count() == 0:
				part_format = self(name=format_name)
				part_format.save()

	@classmethod
	def check_and_get_part_format(self, format_name):
		if not format_name in self.possible_parts_formats_names:
			format_name = 'text'
		return self.objects.get(name=format_name)

class Part_Type(models.Model):

	name = models.CharField(max_length=255)
	format = models.ForeignKey(Part_Format, models.PROTECT)
	language = models.ForeignKey(Language, models.PROTECT)

	add_new_item_pathname = 'add_new_part_type'
	list_namepath = 'parts_types'

	def __str__(self):
		if self.language.code:
			language_code = self.language.code.upper()
		else:
			language_code = '-'

		return '({}) {} (Format: {})'.format(language_code, self.name.capitalize(), self.format)

	def get_absolute_url(self):
		return reverse('update_part_type', kwargs={'pk': self.id})

	def get_list_url(self):
		return reverse(self.list_namepath)

	def get_delete_url(self):
		return reverse('delete_part_type', kwargs={'pk': self.id})

	@classmethod
	def get_add_new_item_into_end_url(self):
		return reverse(self.add_new_item_pathname)

	@property
	def ready_to_delete(self):
		parts_in_elements_count = Parts.objects.filter(part__type=self).count()
		parts_types_in_sets_types_count = Parts_Types.objects.filter(type=self).count()
		return parts_in_elements_count < 1 or parts_types_in_sets_types_count < 1

	def delete(self):
		if self.ready_to_delete:
			super().delete()
		return self.get_list_url()

	def check_imported_part_type(self, part_type_properties):
		part_format = part_type_properties.get("format")
		part_language = part_type_properties.get("language")
		if part_format and "name" in part_format and part_language and "code" in part_language:
			return part_format["name"] == self.format.name and part_language["code"] == self.language.code
		else:
			return False

	@classmethod
	def find_or_create_part_type(self, part_type_properties):
		part_format = part_type_properties.get("format")
		part_language = part_type_properties.get("language")
		part_name = part_type_properties.get("name")

		if part_name and part_format and "name" in part_format and part_language and "code" in part_language:
			parts_types = self.objects.filter(name=part_name,
											format__name=part_format["name"],
											language__code=part_language["code"])
			if parts_types.count() > 0:
				part_type = parts_types[0]
			else:
				part_format = Part_Format.check_and_get_part_format(part_format["name"])
				part_language = Language.find_or_create_language(part_language["code"])
				if part_name == '':
					part_name = '{} {}'.format(part_language.__str__().capitalize(), part_format)
				part_type = self(format=part_format,
								language=part_language,
								name=part_name)
				part_type.save()
		else:
			if not (part_format and "name" in part_format):
				part_format = Part_Format.check_and_get_part_format('')
			if not (part_language and "code" in part_language):
				part_language = Language.get_default_language()
			if not part_name or part_name == '':
				part_name = '{} {}'.format(part_language.__str__().capitalize(), part_format)
			part_type = self(format=part_format,
							language=part_language,
							name=part_name)
			part_type.save()
		
		return part_type

class Parts_Types(List_Model):

	set_type = models.ForeignKey(Set_Type, models.PROTECT)
	position = models.IntegerField(null=False)
	type = models.ForeignKey(Part_Type, models.PROTECT)
	main_color = models.CharField(max_length=255, null=True)
	background_color = models.CharField(max_length=255, null=True)

	container_field_name = "set_type"
	change_position_url = "change_part_type_position"
	add_new_item_pathname = "add_new_part_type_into_set_type"

	def __str__(self):
		return str(self.type)

	@property
	def position_with_type(self):
		return '{}. {}'.format(self.position, self.type)

	def get_absolute_url(self):
		return reverse('update_set_type', kwargs={'pk': self.__getattribute__(self.container_field_name).id})

	def get_delete_url(self):
		return reverse('delete_path_type_out_of_set_type', kwargs={'pk': self.id})

	@classmethod
	def get_add_new_item_into_end_url(self, set_type):
		return reverse(self.add_new_item_pathname, kwargs={'container': set_type.id})

	@property
	def deleting_is_forbiden(self):
		return self.position < self.__class__.objects.filter(set_type=self.set_type).count()

	@classmethod
	def change_position(self, *args, **kwargs):
		# Only up and down changing are possible now.
		# Changing parts types' order changes parts' positions in related sets!
		set_type = kwargs['container']
		position = kwargs['position']
		direction = kwargs['direction']
		if direction in ['up', 'down']:
			super().change_position(*args, **kwargs)
			parts_in_elements = Parts.objects.filter(element__type=set_type, position=position)
			for part_in_element in parts_in_elements:
				kwargs['container'] = part_in_element.element.id
				part_in_element.__class__.change_position(*args, **kwargs)
		return Set_Type.objects.get(id=set_type).get_absolute_url()

	def delete(self):
		# '''Part type's deleting out the set type is possible,
		# only when there is no one element including this part type
		# and parts with this part type's position is last in this set types' list.
		# If you want to delete a part type,
		# delete all parts with this part type in elements (or entire elements)
		# and push down this part type's position to the last position in this set types' list!'''
		
		if not self.deleting_is_forbiden:
			parts_in_elements = Parts.objects.filter(element__type=self.set_type,
													part__type=self.type,
													position=self.position)
			
			for part_in_element in parts_in_elements:
				part_in_element.delete()
			super().delete()
		return self.container.get_content_list_url()

	def add_part_with_part_type_into_elements(self):
		elements = Element.objects.filter(type=self.set_type)
		for element in elements:
			part = Part(type=self.type)
			part.save()
			part_in_element = Parts(element=element,
									part=part,
									position=self.position)
			part_in_element.save()

	@classmethod
	def check_imported_parts_types(self, set_type, parts_types):
		parts_types_for_set_type = self.objects.filter(set_type=set_type)
		if parts_types_for_set_type.count() == len(parts_types):
			for part_type in parts_types:
				found_parts_types = parts_types_for_set_type.filter(position=part_type["position"])
				if found_parts_types.count() > 0:
					found_part_type = found_parts_types[0]
					if not found_part_type.type.check_imported_part_type(part_type["type"]):
						return False
				else:
					return False
			return True
		else:
			return False

	@classmethod
	def save_color(self, input_dict):
		id = input_dict["id"]
		type = input_dict["type"]
		color = input_dict["color"]
		part_type_in_set_type = self.objects.get(id=id)
		part_type_in_set_type.__dict__[type] = color
		part_type_in_set_type.save()
		return '{} for {} has been saved'.format(type.capitalize().replace('_',' '), part_type_in_set_type)

class Set(Item_Model):

	title = models.CharField(max_length=255)
	type = models.ForeignKey(Set_Type, models.PROTECT)
	abstract = models.TextField(blank=True, null=True)
	created_at = models.DateTimeField(auto_now_add=True)
	storage = models.BooleanField(default=False)
	notes_available = models.BooleanField(default=False)
	color = models.CharField(max_length=255, null=True)

	def __str__(self):
		return '{} (Set type: {})'.format(self.title, self.type)

	@property
	def title_with_language(self):
		return '({}) {}'.format(self.type.language.code.upper(), self)

	def get_absolute_url(self):
		return reverse('show_set', kwargs={'pk': self.id})

	def get_content_list_url(self):
		return reverse('show_set_elements', kwargs={'set': self.id})

	def get_containers_list_url(self):
		return reverse('show_set_topics', kwargs={'pk': self.id})

	def get_insert_content_item_into_container_url(self):
		return reverse('insert_element_into_set', kwargs={'pk': self.id})

	def get_delete_url(self):
		return reverse('delete_set', kwargs={'pk': self.id})

	@staticmethod
	def get_storage_title_for_type(set_type):
		return "Storage for elements for \"{}\" set type".format(str(set_type))

	@classmethod
	def get_storage_set_for_type(self, set_type):

		def create_storage_set_for_type(set_type, storage_title_for_type, storage_topic_for_sets):
			storage_set_for_type = self(title=storage_title_for_type,
										type=set_type,
										storage=True)
			storage_set_for_type.save()
			sets_in_storage_topic_for_sets_count = Sets.objects.filter(topic=storage_topic_for_sets.id).count()			
			storage_set_for_type_in_topic = Sets(topic=storage_topic_for_sets,
												set=storage_set_for_type,
												position=sets_in_storage_topic_for_sets_count+1)
			storage_set_for_type_in_topic.save()
			return storage_set_for_type

		def insert_storage_set_in_storage_topic(storage_topic_for_sets_id, set_id):
			Topics.insert_item(pk=storage_topic_for_sets_id,
								to_delete=True,
								content_items_ids_to_insert=[set_id])

		def change_sets_props(queryset, change_title=False):
			increment = 0
			for set in queryset:
				container_set = set.set
				increment += 1
				if change_title:
					container_set.title += increment
				container_set.storage = False
				container_set.save()

		storage_title_for_type = self.get_storage_title_for_type(set_type)
		storage_topic_for_sets = Topic.get_storage_topic_for_sets_without_topic()
		sets_basic_queryset = Sets.objects.filter(set__storage=True, set__type=set_type).order_by("set__created_at")
		sets_with_type = sets_basic_queryset.filter(topic=storage_topic_for_sets)
		sets_with_type_count = sets_with_type.count()
		
		if sets_with_type_count == 1:
			return sets_with_type[0].set
		
		elif sets_with_type_count < 1:

			sets_with_type_out_storage_topic = sets_basic_queryset
			sets_with_type_out_storage_topic_count = sets_with_type_out_storage_topic.count()

			if sets_with_type_out_storage_topic_count == 1:
				set_with_type = sets_with_type_out_storage_topic[0].set
				insert_storage_set_in_storage_topic(storage_topic_for_sets.id, set_with_type.id)
				return set_with_type.set

			elif sets_with_type_out_storage_topic_count < 1:
				sets_with_type_with_title = sets_with_type_out_storage_topic.filter(set__title=storage_title_for_type)
				sets_with_type_with_title_count = sets_with_type_with_title.count()
				
				if sets_with_type_with_title_count == 1:
					set_with_type_with_title = sets_with_type_with_title[0].set
					insert_storage_set_in_storage_topic(storage_topic_for_sets.id, set_with_type_with_title.id)
					return set_with_type_with_title.set

				elif sets_with_type_with_title_count < 1:
					return create_storage_set_for_type(set_type, storage_title_for_type, storage_topic_for_sets)

				elif sets_with_type_with_title_count > 1:
					set_with_type_with_title = sets_with_type_with_title[0].set
					change_sets_props(sets_with_type_with_title[1:], change_title=True)
					return set_with_type_with_title.set

			elif sets_with_type_out_storage_topic_count > 1:
				set_with_type = sets_with_type_out_storage_topic[0].set
				insert_storage_set_in_storage_topic(storage_topic_for_sets.id, set_with_type_with_title.id)
				change_sets_props(sets_with_type_out_storage_topic[1:], change_title=True)
				return set_with_type.set

		elif sets_with_type_count > 1:
			sets_with_type_with_title = sets_with_type.filter(set__title=storage_title_for_type)
			sets_with_type_with_title_count = sets_with_type_with_title.count()

			if sets_with_type_with_title_count == 1:
				set_with_type = sets_with_type_with_title[0].set
				change_sets_props(sets_with_type.exclude(set__title=storage_title_for_type), change_title=True)
				return set_with_type.set

			elif sets_with_type_with_title_count < 1:
				set_with_type = sets_with_type[0].set
				set_with_type.title = storage_title_for_type
				set_with_type.save()
				return set_with_type.set

			elif sets_with_type_with_title_count > 1:
				set_with_type = sets_with_type_with_title[0].set
				change_sets_props(sets_with_type_with_title[1:], change_title=True)
				return set_with_type.set

	def delete_out_of_all_topics(self, *args, **kwargs):
		
		def get_sets_in_topics(set):
			return Sets.objects.filter(set=set)

		def delete_sets_in_topics(set):
			sets_in_topics = get_sets_in_topics(set)
			storage = False
			for set_in_topic in sets_in_topics:
				if set_in_topic.topic.storage:
					storage = True
				Sets.delete_item(pk=set_in_topic.id)
			if not storage:
				delete_sets_in_topics(set)
		
		back_redirect_url = self.type.get_containers_list_url()
		delete_sets_in_topics(self)
		self.delete()
		return back_redirect_url

	@classmethod
	def change_notes_availability(self, id):
		sets = self.objects.filter(id=id)
		sets_count = sets.count()
		if sets_count > 1:
			response_text = "There are more than one {} with this ID".format(model_name)
		elif sets_count < 1:
			response_text = "There is no {} with this ID".format(model_name)
		else:
			set = sets[0]
			set.notes_available = not set.notes_available
			set.save()
			response_text = '{} is{} available for notes'.format(set, ' not' if not set.notes_available else '')
		return response_text

	@classmethod
	def add_new_element(self, set_id, direction='end', return_url=True):
		set = self.objects.select_related("type").get(id=set_id)

		new_element = Element()
		new_element.type = set.type
		new_element.save()

		elements_in_set_count = Elements.objects.filter(set=set_id).count()
		
		new_element_in_set = Elements(set=set,
							element=new_element,
							position=elements_in_set_count + 1)
		new_element_in_set.save()

		parts_in_element = new_element.create_parts()

		new_element_in_set = Elements.change_item_position(container=set_id,
															position=new_element_in_set.position,
															direction=direction)		

		if return_url:
			if new_element_in_set.parts_in_element_exisit:
				return new_element_in_set.get_correct_set_element_first_part_url()
			else:
				return set.get_content_list_url()
		else:
			return parts_in_element, new_element

	@classmethod
	def save_element_as_note(self, input_dict):

		def handle_input_dict(input_dict):
			input_parts = {}
			for input_part in input_dict["parts"]:
				input_parts[int(input_part["position"])] = {}
				for field in input_part["fields"]:
					input_parts[int(input_part["position"])][field["type"]] = field["data"]
			return input_parts

		input_parts = handle_input_dict(input_dict)

		parts_in_element, new_element = self.add_new_element(input_dict["set"], return_url=False)
		for part_in_element in parts_in_element:
			part = part_in_element.part
			part.content = input_parts[part_in_element.position]["content"]
			if input_parts[part_in_element.position]["comment"] != '':
				part.comment = input_parts[part_in_element.position]["comment"]
			part.save()

		abstract = input_dict["abstract"]

		if abstract != '':
			new_element.abstract = abstract
			new_element.save()

		return "Element has been saved as a note"

	def get_export_native_format_url(self):
		return '{}?set_id={}'.format(reverse('export_native_formated_set'), self.id)

	def get_export_common_format_url(self):
		return reverse('export_common_formated_set', kwargs={"set": self.id})

	@classmethod
	def import_common_formated_set(self, form):
		# todo optimize request
		importing_text = form.cleaned_data['raw_text']
		element_separator = form.cleaned_data['element_separator']
		part_separator = form.cleaned_data['part_separator']
		google_translate_formated = form.cleaned_data['google_translate_formated']
		
		topic = form.data["topic"]
		topics = Topics.objects.select_related("topic").filter(id=topic)
		if topics.count() < 1:
			topic = Topic.get_storage_topic_for_sets_without_topic()
			topic = topic.id
		else:
			topic = topics[0].topic.id

		new_set = form.save()

		set_type = form.cleaned_data['type']
		parts_types = set_type.parts_types()
		parts_quantity = parts_types.count()
		
		raw_elements = importing_text.split(element_separator)
		elements = []
		for raw_element in raw_elements:
			if raw_element:
				parts = raw_element.split(part_separator)
				if google_translate_formated:
					parts = parts[2:]
				elements.append(parts)

		for element_position_index in range(len(elements)):
			new_element = Element()
			new_element.type = new_set.type
			new_element.save()
			element = elements[element_position_index]
			
			for part_position_index in range(parts_quantity):
				if part_position_index < len(element):
					part_content = element[part_position_index]
				else:
					part_content = None

				new_part = Part()
				new_part.content = part_content
				new_part.type = parts_types[part_position_index].type
				style = {}
				for color in ['main_color', 'background_color']:
					if parts_types[part_position_index].__getattribute__(color):
						style[color] = parts_types[part_position_index].__getattribute__(color)
				if len(style) > 0:
					new_part.style = json.dumps(style)
				new_part.save()

				new_part_in_element = Parts()
				new_part_in_element.part = new_part
				new_part_in_element.element = new_element
				new_part_in_element.position = part_position_index + 1
				new_part_in_element.save()

			new_element_in_set = Elements()
			new_element_in_set.element = new_element
			new_element_in_set.set = new_set
			new_element_in_set.position = element_position_index + 1
			new_element_in_set.save()

		Sets.put_set_into_topic(topic=topic, set=new_set.id)
		return new_set.get_content_list_url()

	@classmethod
	def import_native_formated_set(self, topic, imported_set):
		# todo optimize request
		set_type = Set_Type.get_imported_set_type(imported_set)
		if set_type:
			set_title = imported_set["set"]["set_properties"]["title"]
			set_abstract = imported_set["set"]["set_properties"].get("abstract")
			set = self(type=set_type,
						title=set_title,
						abstract=set_abstract)
			set.save()
			Sets.put_set_into_topic(topic=topic, set=set.id)

			elements = imported_set.get("elements")
			if elements:
				Elements.import_formated_elements(set, elements)
				return set.get_content_list_url()
			else:
				return set_type.get_absolute_url()
		else:
			return reverse('import_native_formated_set') # format mistake

	@classmethod
	def generate_export_file(self, export_type, request):

		class Generate_File_Basic:

			file_resolution = None

			@classmethod
			def generate(self, set_class, request):
				self.request = request
				self.set_class = set_class
				data = self.get_set_data(request)
				exporting_filepath = self.create_file(data)
				return data, exporting_filepath

			@classmethod
			def return_file(self, create_file_function):
				def	wrapped(self, data):
					language, title, type_name = create_file_function(self, data)
					folder = 'export_files'
					dt = timezone.localtime().strftime("%Y.%m.%d %H-%M")
					filename = '({}) {} - {} {}'.format(language.upper(), title, type_name, dt)
					exporting_filepath = '{}/{}.{}'.format(folder, filename, self.file_resolution)
					self.write_data_in_file(exporting_filepath, data)
					return exporting_filepath
				return wrapped

		class Generate_Native_Formated_File(Generate_File_Basic):

			file_resolution = 'json'

			@classmethod
			def get_set_data(self, request):
				from .views import Set_With_Part_Types_Export_ViewSet
				from .views import Elements_List_Export_ViewSet

				set_response = Set_With_Part_Types_Export_ViewSet().list(request)
				elements_response = Elements_List_Export_ViewSet().list(request)
				data = {'version': 0,
						'set': set_response.data,
						'elements': elements_response.data}
				return data

			@classmethod
			@Generate_File_Basic.return_file
			def create_file(self, data):
				set_properties = data["set"]["set_properties"]
				language = set_properties["type"]["language"]["code"]
				title = set_properties["title"]
				type_name = set_properties["type"]["name"]
				return language, title, type_name

			@classmethod
			def write_data_in_file(self, exporting_filepath, data):
				with open(exporting_filepath, 'w', encoding='utf-8') as file:
					json.dump(data, file, ensure_ascii=False)

		class Generate_Common_Formated_File(Generate_File_Basic):

			file_resolution = 'txt'

			@classmethod
			def get_set_data(self, request):
				return request.POST.get("raw_text", "No data to export")

			@classmethod
			@Generate_File_Basic.return_file
			def create_file(self, data):
				set_id = self.request.POST.get("set")
				set = self.set_class.objects.prefetch_related('type').get(id=set_id)
				language = set.type.language.code
				title = set.title
				type_name = set.type.name
				return language, title, type_name

			@classmethod
			def write_data_in_file(self, exporting_filepath, data):
				with open(exporting_filepath, 'w') as file:
					file.write(data.replace('\r\n', '\n'))

		export_classes = {'native': Generate_Native_Formated_File,
						'common': Generate_Common_Formated_File}
		
		data, exporting_filepath = export_classes[export_type].generate(self, request)
		filename = os.path.basename(exporting_filepath)
		response = HttpResponse(FileWrapper(open(exporting_filepath, 'rb')),
								content_type=mimetypes.guess_type(filename)[0])

		response['Content-Length'] = os.path.getsize(exporting_filepath)
		response['Content-Disposition'] = "attachment; filename={}".format(filename)
		os.remove(exporting_filepath)
		return response

class Sets(List_Model):

	topic = models.ForeignKey(Topic, models.PROTECT)
	position = models.IntegerField(null=False)
	set = models.ForeignKey(Set, models.PROTECT)

	container_field_name = 'topic'
	content_field_name = 'set'
	container_container_model = Subject
	change_position_url = 'change_sets_position'
	add_new_item_pathname = 'add_new_set_into_topic'

	def get_absolute_url(self):
		return reverse('show_topic_sets', kwargs={'topic': self.topic.id})

	def get_delete_url(self):
		return reverse('delete_topic_set', kwargs={'pk': self.id})

	def get_add_new_item_into_end_url(self):
		return reverse(self.add_new_item_pathname, kwargs={'container': self.topic.id,
														'direction': 'end'})

	def set_container(self, container_object):
		self.topic = container_object

	def set_content(self, content_object):
		self.set = content_object

	def delete(self):
		back_redirect_url = self.container.get_content_list_url()
		set_in_other_topics = self.__class__.objects.filter(set=self.set.id)
		set_in_other_topics_count = set_in_other_topics.count()
		if set_in_other_topics_count > 1:
			super().delete()
		else:
			storage_topic_for_sets = Topic.get_storage_topic_for_sets_without_topic()
			if self.topic == storage_topic_for_sets:
				elements_in_set = Elements.objects.filter(set=self.set)
				for element in elements_in_set:
					element.delete() # Remove or delete element
				super().delete() # Delete set outta subject
				playlists = Sets_In_Playlists.objects.filter(set=self.set)
				for set_number in range(playlists.count()):
					playlists[set_number].delete()
				self.set.delete() # Delete set				
			else: # Move this set to the storage topic for sets without topics
				Sets.insert_item(pk=storage_topic_for_sets.id,
								to_delete=False,
								content_items_ids_to_insert=[self.id])
				super().delete() # Delete set in topic

		return back_redirect_url

	@classmethod
	def put_set_into_topic(self, topic, set):
		sets = self.objects.filter(topic=topic)
		position = sets.count() + 1
		set_in_topic = self(topic_id=topic, set_id=set, position=position)
		set_in_topic.save()

class Element(Item_Model):
	abstract = models.TextField(blank=True, null=True)
	created_at = models.DateTimeField(auto_now_add=True)
	correct_answers = models.IntegerField(default=0)
	wrong_answers = models.IntegerField(default=0)
	type = models.ForeignKey(Set_Type, models.PROTECT)

	def __str__(self):
		base_string = 'ID: {} (Element type: {})'		
		return base_string.format(self.id, self.type)

	def get_absolute_url(self):
		return reverse('show_element', kwargs={'pk': self.id})

	def get_content_list_url(self):
		return reverse('show_element_parts', kwargs={'element': self.id})

	def get_parts(self):
		parts = Parts.objects.filter(element=self).order_by('position')
		if parts.count() > 0:
			return parts
		else:
			return self.create_parts()

	def get_containers_list_url(self):
		return reverse('show_element_sets', kwargs={'pk': self.id})

	def get_correct_parts_dictionary(self):
		parts = self.get_parts()
		if parts.count() > 0:
			return {'element': self.id,
					'part_position': parts[0].position,
					'part_direction': 'base'}
		else:
			return False

	def get_correct_element_parts_url(self):
		correct_parts_dictionary = self.get_correct_parts_dictionary()
		if correct_parts_dictionary:
			return reverse('correct_element_parts', kwargs=correct_parts_dictionary)
		else:
			return False #Create part url

	def get_pronounce_element_abstract_text_url(self):
		return self.get_pronunce_url(self.abstract, self.type.language.code.lower())

	@property
	def parts_in_element_exisit(self):
		return Parts.objects.filter(element=self).count() > 0

	def create_parts(self):
		parts_in_element = []
		parts_types = Parts_Types.objects.select_related('type').filter(set_type=self.type).order_by('position')
		for part_type in parts_types:
			part = Part()
			part.type = part_type.type
			part.save()
			part_in_element = Parts()
			part_in_element.position = part_type.position
			part_in_element.element = self
			part_in_element.part = part
			part_in_element.save()
			parts_in_element.append(part_in_element)
		return parts_in_element

	@classmethod
	def import_formated_element(self, set_type, imported_element, parts_types):
		element = imported_element.get("element")
		if element:
			abstract = element.get("abstract")
		else:
			abstract = None
		element = self(abstract=abstract, type=set_type)
		element.save()
		imported_parts = imported_element.get("parts")
		Parts.import_formated_parts(element, imported_parts, parts_types)
		return element

class Elements(List_Model):
	set = models.ForeignKey(Set, models.PROTECT)
	position = models.IntegerField(null=False)
	element = models.ForeignKey(Element, models.PROTECT)

	container_field_name = 'set'
	content_field_name = 'element'
	container_container_model = Topic
	change_position_url = 'change_elements_position'
	add_new_item_pathname = 'add_new_element_into_set'

	def get_absolute_url(self):
		return reverse('show_set_elements', kwargs={'set': self.set.id})

	def get_delete_url(self):
		return reverse('delete_set_element', kwargs={'pk': self.id})

	def get_add_new_item_into_end_url(self):
		return reverse(self.add_new_item_pathname, kwargs={'container': self.set.id,
															'direction': 'end'})

	def set_container(self, container_object):
		self.set = container_object

	def set_content(self, content_object):
		self.element = content_object

	@property
	def parts_in_element_exisit(self):
		return self.element.parts_in_element_exisit		

	def get_correct_set_element_first_part_url(self):

		if self.parts_in_element_exisit:
			correct_parts_dictionary = self.element.get_correct_parts_dictionary()
			correct_parts_dictionary["set"] = self.set.id
			correct_parts_dictionary["element"] = self.position
			correct_parts_dictionary["element_direction"] = 'base'
			correct_parts_dictionary["part_position"] = 1

			return reverse('correct_set_element_parts', kwargs=correct_parts_dictionary)

		else:
			return False

	def get_parts_with_urls(self):
		parts = self.element.get_parts()
		for part in parts:
			correct_parts_dictionary = self.element.get_correct_parts_dictionary()
			correct_parts_dictionary["set"] = self.set.id
			correct_parts_dictionary["element"] = self.position
			correct_parts_dictionary["element_direction"] = 'base'
			correct_parts_dictionary["part_position"] = part.position
			main_color = part.part.main_color
			if main_color:
				part.main_color = main_color
			
			if part.part.type_format == "text":
				part.show_part_url = part.edit_part_url = self.get_correct_set_element_parts_url(correct_parts_dictionary)
			elif part.part.type_format == "url":
				part.edit_part_url = self.get_correct_set_element_parts_url(correct_parts_dictionary)
				part.show_part_url = part.part.content if part.part.content else part.edit_part_url
		return parts

	@staticmethod
	def get_correct_set_element_parts_url(correct_parts_dictionary):
		return reverse('correct_set_element_parts', kwargs=correct_parts_dictionary)

	def delete(self):
		back_redirect_url = self.container.get_content_list_url()
		elements_in_other_sets = self.__class__.objects.filter(element=self.element.id)
		elements_in_other_sets_count = elements_in_other_sets.count()
		if elements_in_other_sets_count > 1:
			super().delete()
		else:
			storage_set_for_elements_with_set_type = Set.get_storage_set_for_type(self.set.type)
			if self.set == storage_set_for_elements_with_set_type:
				parts_in_elments = Parts.objects.filter(element=self.element)
				for part in parts_in_elments:
					part.delete() # Remove or delete part
				super().delete() # Delete element in set
				self.element.delete() # Delete element
			else: # Move this set to the storage topic for sets without topics
				Elements.insert_item(pk=storage_set_for_elements_with_set_type.id,
									to_delete=False,
									content_items_ids_to_insert=[self.id])
				super().delete() # Delete element in set

		return back_redirect_url

	@classmethod
	def import_formated_elements(self, set, imported_elements):
		parts_types = Parts_Types.objects.filter(set_type=set.type).order_by("position")
		for i in range(len(imported_elements)):
			imported_element = imported_elements[i]
			position = imported_element.get("position")
			if not position:
				position = i + 1
				imported_element["position"] = position
			element = Element.import_formated_element(set.type, imported_element, parts_types)
			element_in_set = self(element=element,
									set=set,
									position=position)
			element_in_set.save()
		return True

class Part(Item_Model):

	content = models.TextField(blank=True, null=True)
	type = models.ForeignKey(Part_Type, models.PROTECT)
	style = models.TextField(blank=True, null=True)
	comment = models.TextField(blank=True, null=True)

	text_abstract = "comment"

	def __str__(self):
		return '{} (Part type: {})'.format(self.content, self.type)

	@property
	def type_format(self):
		return self.type.format.name

	def get_absolute_url(self):
		return reverse('show_part', kwargs={'pk': self.id})

	def get_correct_part_url(self):
		if self.type_format == "text":
			return reverse('correct_part', kwargs={'pk': self.id})
		elif self.type_format == "url":
			return reverse('correct_part', kwargs={'pk': self.id}) # create simple text editor for link's correction

	@property
	def main_color(self):
		main_color = False
		if self.style:
			main_color = json.loads(self.style).get("main_color")
		return main_color

	def get_containers_list_url(self):
		return reverse('show_part_elements', kwargs={'pk': self.id})

	def get_content_list_url(self):
		return False

	@staticmethod
	def get_correct_set_element_parts_url(correct_parts_dictionary):
		return reverse('correct_set_element_parts', kwargs=correct_parts_dictionary)

	def get_pronounce_part_text_url(self):
		return self.get_pronunce_url(self.content, self.type.language.code.lower())

	def get_pronounce_part_comment_text_url(self):
		return self.get_pronunce_url(self.comment, self.type.language.code.lower())

	@classmethod
	def create_empty_part(self, part_type):
		part = self(type=part_type)
		part.save()
		return part

	@classmethod
	def import_formated_part(self, imported_part, part_type):
		part = self(type=part_type,
					content=imported_part.get("content"),
					style=imported_part.get("style"),
					comment=imported_part.get("comment"))
		part.save()
		return part

class Parts(List_Model):

	element = models.ForeignKey(Element, models.PROTECT)
	position = models.IntegerField(null=False)
	part = models.ForeignKey(Part, models.PROTECT)

	container_field_name = 'element'
	content_field_name = 'part'
	container_container_model = Set

	def delete(self):
		parts_in_other_elements = self.__class__.objects.filter(part=self.part.id)
		parts_in_other_elements_count = parts_in_other_elements.count()
		if parts_in_other_elements_count > 1:
			super().delete()
		else:
			super().delete()
			self.part.delete()

	def get_absolute_url(self):
		pass

	@classmethod
	def import_formated_parts(self, element, imported_parts, parts_types):
		parts_in_element_count = parts_types.count()
		if imported_parts:
			for i in range(len(imported_parts)):
				imported_part = imported_parts[i]
				position = imported_part.get("position")
				if not position:
					position = i + 1
				if position <= parts_in_element_count:
					imported_part = imported_part.get("part")
					part_type = parts_types[i].type
					if imported_part:
						part = Part.import_formated_part(imported_part, part_type)
					else:
						part = Part.create_empty_part(part_type)
					part_in_element = self(element=element,
											position=position,
											part=part)
					part_in_element.save()
		else:
			for i in range(parts_in_element_count):
				part = Part.create_empty_part(parts_types[i])
				part_in_element = self(element=element,
										position=i+1,
										part=part)
				part_in_element.save()

class User(models.Model):

	name = models.CharField(max_length=255)
	language = models.ForeignKey(Language, models.PROTECT)
	timezone = models.CharField(max_length=255, null=True, blank=True)

	def __str__(self):
		return self.name

	def get_absolute_url(self):
		return reverse('user_profile')

	@classmethod
	def get_user(self):
		users = self.objects.all()
		users_count = users.count()
		if users_count > 0:
			return users[0]
		elif users_count == 0:
			return False
	
	@classmethod
	def get_user_timezone(self):
		user = self.get_user()
		if user:
			return user.timezone
		else:
			return False

	@classmethod
	def get_user_language(self):
		user = self.get_user()
		if user and user.language.code:
			return user.language.code
		else:
			return Language.default_defined_langauge_code

	@classmethod
	def ensure_languages_translation(self, form):
		previous_language = self.get_user_language()
		form.save()
		next_language = self.get_user_language()
		if next_language != Language.undefined_language_code and next_language != previous_language:
			languages = Language.objects.all()
			for language in languages:
				if language.code != Language.undefined_language_code:
					language.translation_name = Language.get_language_info(language.english_name)['name_translated'].lower()
					language.save()

	@classmethod
	def save_timezone(self, timezone):
		user = self.get_user()
		user.timezone = timezone
		user.save()

class Playlist(List_Model, Item_Model):

	position = models.IntegerField(null=False)
	title = models.CharField(max_length=255)
	language = models.ForeignKey(Language, models.PROTECT)
	abstract = models.TextField(blank=True, null=True)	
	created_at = models.DateTimeField(auto_now_add=True)
	color = models.CharField(max_length=255, null=True)

	change_position_url = 'change_playlist_position'
	add_new_item_pathname = 'add_new_playlist'
	list_namepath = 'show_playlists'
	item_namepath = 'show_playlist'
	item_details_namepath = 'show_playlist'
	delete_item_namepath = 'delete_playlist'
	content_list_path = 'show_playlist_sets'
	insert_content_item = 'insert_set_into_playlist'

	def __str__(self):
		return self.title

	def get_absolute_url(self):
		return reverse(self.item_namepath, kwargs={'pk': self.id})

	def get_details_url(self):
		return reverse(self.item_details_namepath, kwargs={'pk': self.id})

	def get_delete_url(self):
		return reverse(self.delete_item_namepath, kwargs={'pk': self.id})

	def get_content_list_url(self):
		return reverse(self.content_list_path, kwargs={'playlist': self.id})

	def get_item_id(self):
		return self.id

	@classmethod
	def get_list_url(self):
		return reverse(self.list_namepath)

	def get_insert_content_item_into_container_url(self):
		return reverse(self.insert_content_item, kwargs={'pk': self.pk})

	def get_change_position_url(self, direction):
		return reverse(self.change_position_url, kwargs={'position': self.position,
														'direction': direction})

	def delete(self):
		back_redirect_url = self.get_list_url()
		sets_in_playlist = Sets_In_Playlists.objects.filter(playlist=self)
		for set_in_playlist in sets_in_playlist:
			set_in_playlist.delete()
		super().delete()
		return back_redirect_url

	@classmethod
	def get_add_new_item_into_end_url(self):
		return reverse(self.add_new_item_pathname, kwargs={'direction': 'end'})

	@classmethod
	def get_items(self, *args, **kwargs):
		return self.objects.all()

	def get_content_items(self):
		return Sets_In_Playlists.objects.filter(playlist=self)

class Sets_In_Playlists(List_Model):

	playlist = models.ForeignKey(Playlist, models.PROTECT)
	position = models.IntegerField(null=False)
	set = models.ForeignKey(Set, models.PROTECT)

	container_field_name = 'playlist'
	content_field_name = 'set'
	
	change_position_url = 'change_playlist_sets_position'
	list_namepath = 'show_playlist_sets'
	delete_item_namepath = 'delete_playlist_set'

	def __str__(self):
		return str(self.set)

	def get_absolute_url(self):
		return reverse(self.list_namepath, kwargs={'playlist': self.playlist.id})

	def get_delete_url(self):
		return reverse(self.delete_item_namepath, kwargs={'pk': self.id})

	def get_add_new_item_into_end_url(self):
		return reverse(self.change_position_url, kwargs={'container': self.get_container_title(),
														'position': 1,
														'direction': 'end'})
		
	def set_container(self, container_object):
		self.playlist = container_object

	def set_content(self, content_object):
		self.set = content_object

	def delete(self):
		back_redirect_url = self.container.get_content_list_url()
		super().delete()
		return back_redirect_url