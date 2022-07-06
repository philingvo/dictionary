import pytz
import json
from rest_framework.response import Response
from django.shortcuts import render
from django.views.generic.base import View
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView
from django.views.generic.edit import DeleteView
from django.views.generic.edit import UpdateView
from django.views.generic.edit import BaseUpdateView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.urls import reverse_lazy
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from .models import *
from .forms import *
from .serializers import *


# https://www.django-rest-framework.org/api-guide/viewsets/
class Subjects_List_ViewSet(viewsets.ViewSet):

	def list(self, request):
		storage = request.GET.get('storage', False)
		queryset = Subject.objects.filter(storage=storage).order_by('position')
		serializer = Subject_serializer(queryset, many=True)
		return Response(serializer.data)

class Topics_List_ViewSet(viewsets.ViewSet):

	def list(self, request):
		subject_id = request.GET.get('subject_id')
		queryset = Topics.objects.filter(subject=subject_id).order_by('position')
		serializer = Topics_serializer(queryset, many=True)
		return Response(serializer.data)

class Sets_List_ViewSet(viewsets.ViewSet):

	def list(self, request):
		topic_id = request.GET.get('topic_id')
		queryset = Sets.objects.filter(topic=topic_id).order_by('position')
		serializer = Sets_serializer(queryset, many=True)
		return Response(serializer.data)

class Sets_In_Playlist_List_ViewSet(viewsets.ViewSet):

	def list(self, request):
		playlist_id = request.GET.get('playlist_id')
		queryset = Sets_In_Playlists.objects.filter(playlist=playlist_id).order_by('position')
		serializer = Sets_In_Playlist_serializer(queryset, many=True)
		return Response(serializer.data)

class Sets_List_By_Topics_ID_ViewSet(viewsets.ViewSet):

	def list(self, request):
		topics_id = request.GET.get('topics_id')
		topic = Topics.objects.get(id=topics_id)
		request.GET._mutable = True
		request.GET['topic_id'] = topic.topic
		return Sets_List_ViewSet().list(request)

class Sets_List_For_The_Same_Set_Type_ViewSet(viewsets.ViewSet):

	def list(self, request):
		set_id = request.GET.get('set_id')
		set = Set.objects.prefetch_related('type').get(id=set_id)
		queryset = Set.objects.filter(type=set.type).order_by('-created_at')
		serializer = Set_serializer(queryset, many=True)
		return Response(serializer.data)

class Parts_Types_ViewSet(viewsets.ViewSet):

	def list(self, request):
		set_id = request.GET.get('set_id')
		set = Set.objects.prefetch_related('type').get(id=set_id)
		return self.get_parts_types(set.type.id)

	def get_parts_types(self, set_type_id):
		queryset = Parts_Types.objects.filter(set_type__id=set_type_id).order_by('position')
		serializer = Parts_Types_serializer(queryset, many=True)
		return Response(serializer.data)

class Set_ViewSet(viewsets.ViewSet):

	def list(self, request):
		set_id = request.GET.get('set_id')
		queryset = Set.objects.get(id=set_id)
		serializer = Set_serializer(queryset)
		return Response(serializer.data)

class Set_With_Part_Types_ViewSet(viewsets.ViewSet):

	def list(self, request):
		set_response = Set_ViewSet().list(request)
		parts_types_response = Parts_Types_ViewSet().get_parts_types(set_response.data['type']['id'])
		return Response({'set_properties': set_response.data,
						'parts_types': parts_types_response.data})

class Elements_List_ViewSet(viewsets.ViewSet):

	def get_elements_slice(self, queryset, slice_position, slice_length):
		start_element_position = slice_length * (slice_position - 1)
		end_element_position = slice_length * slice_position
		set_length = queryset.count()
		if end_element_position < set_length:
			queryset = queryset[start_element_position:end_element_position]
		else:
			queryset = queryset[start_element_position:]
		return queryset

	def list(self, request):

		def to_int(var):
			try:
				var = int(var)
			except:
				var = None
			return var

		set_id = request.GET.get('set_id')
		slice_position = to_int(request.GET.get('slice_position'))
		slice_length = to_int(request.GET.get('slice_length'))
		queryset = Elements.objects.filter(set=set_id).order_by('position')		
		if slice_position and slice_length:
			queryset = self.get_elements_slice(queryset, slice_position, slice_length)
		serializer = Elements_serializer(queryset, many=True)
		return Response(serializer.data)

class Set_With_Elements_ViewSet(viewsets.ViewSet):

	def list(self, request):
		set_response = Set_With_Part_Types_ViewSet().list(request)
		elements_response = Elements_List_ViewSet().list(request)
		return Response({'set': set_response.data,
						'elements': elements_response.data})

class Set_Length_ViewSet(viewsets.ViewSet):

	def list(self, request):
		set_id = request.GET.get('set_id')
		set_length = Elements.objects.filter(set=set_id).count()
		return Response({'set_length': set_length})

class Parts_List_ViewSet(viewsets.ViewSet):

	def list(self, request):
		element_id = request.GET.get('element_id')
		queryset = Parts.objects.filter(element=element_id)
		serializer = Parts_serializer(queryset, many=True)
		return Response(serializer.data)

class Part_ViewSet(viewsets.ViewSet):

	def list(self, request):
		part_id = request.GET.get('part_id')
		queryset = Part.objects.get(id=part_id)
		serializer = Part_serializer(queryset)
		return Response(serializer.data)

class Set_With_Elements_From_Queue_ViewSet(viewsets.ViewSet):

	def list(self, request):
		attempt = int(request.GET.get('attempt', 1))
		set_queryset = Set.objects.all().order_by('id')
		set_count = set_queryset.count()
		attempt = attempt % set_count
		if attempt == 0:
			attempt = 1
		set_queryset = set_queryset[attempt-1]
		set_id = set_queryset.id
		request.GET._mutable = True
		request.GET['set_id'] = set_id
		return Set_With_Elements_ViewSet().list(request)

class Playlists_List_ViewSet(viewsets.ViewSet):

	def list(self, request):
		queryset = Playlist.objects.all().order_by('position')
		serializer = Playlist_serializer(queryset, many=True)
		return Response(serializer.data)

class Playlist_Set_With_Elements_From_Queue_ViewSet(viewsets.ViewSet):

	def list(self, request):
		attempt = int(request.GET.get('attempt', 1))
		playlists = Playlist.objects.all().order_by('position')

		if playlists.count() == 0:
			return Response({'message': "No playlist has been created yet. Create the first playlist"})

		sets = []
		for playlist_position in range(playlists.count()):
			sets_in_playlist = playlists[playlist_position].get_content_items()
			for set_position in range(sets_in_playlist.count()):
				sets.append([playlist_position, set_position])

		if len(sets) > 0:
			attempt = attempt % len(sets)
			set_in_playlist = sets[attempt]
			playlist_position = set_in_playlist[0] + 1
			set_position = set_in_playlist[1] + 1
			set_in_playlist = Sets_In_Playlists.objects.filter(playlist__position=playlist_position,
																position=set_position)
			set_id = set_in_playlist[0].set.id
			request.GET._mutable = True
			request.GET['set_id'] = set_id
			return Set_With_Elements_ViewSet().list(request)
		else:
			return Response({'message': "Playlists don't contain any set. Add a set in any playlist"})

class Set_With_Part_Types_Export_ViewSet(viewsets.ViewSet):

	def list(self, request):
		set_response = Set_Export_ViewSet().list(request)
		parts_types_response = Parts_Types_Export_ViewSet().get_parts_types(set_response.data['type']['id'])
		del set_response.data['id']
		del set_response.data['type']['id']
		return Response({'set_properties': set_response.data,
						'parts_types': parts_types_response.data})

class Set_Export_ViewSet(viewsets.ViewSet):

	def list(self, request):
		set_id = request.GET.get('set_id')
		queryset = Set.objects.get(id=set_id)
		serializer = Set_Export_serializer(queryset)
		return Response(serializer.data)

class Parts_Types_Export_ViewSet(viewsets.ViewSet):

	def list(self, request):
		set_id = request.GET.get('set_id')
		set = Set.objects.prefetch_related('type').get(id=set_id)
		return self.get_parts_types(set.type.id)

	def get_parts_types(self, set_type_id):
		queryset = Parts_Types.objects.filter(set_type__id=set_type_id).order_by('position')
		serializer = Parts_Types_Export_serializer(queryset, many=True)
		return Response(serializer.data)

class Elements_List_Export_ViewSet(viewsets.ViewSet):

	def list(self, request):
		set_id = request.GET.get('set_id')
		queryset = Elements.objects.filter(set=set_id).order_by('position')
		serializer = Elements_Export_serializer(queryset, many=True)
		return Response(serializer.data)

class CreateView(CreateView):

	fields = '__all__'
	template_name = 'create_form_template.html'

class Create_Subject(CreateView):

	model = Subject

class Create_Topic(CreateView):

	model = Topic

class Put_Topic_Into_Subject(CreateView):

	model = Topics

	def form_valid(self, form):
		topic_in_subject = form.save(commit=False)
		subject = topic_in_subject.subject
		all_topics_for_subject = Topics.objects.filter(subject=subject)
		topic = topic_in_subject.topic
		if all_topics_for_subject.filter(topic=topic).count() == 0:
			topic_in_subject.position = all_topics_for_subject.count() + 1
			topic_in_subject.save()
			return HttpResponseRedirect(reverse('show_subject_topics', kwargs={'subject': subject.id}))
		else:
			self.extra_context = {'error': 'The source "{}" contains the topic "{}" already'.format(subject, topic)}
			return self.render_to_response(self.get_context_data(form=form))

class Create_Set_Type(CreateView):

	model = Set_Type

class Create_Part_Format(CreateView):

	model = Part_Format

class Create_Part_Type(CreateView):

	model = Part_Type

class Set_Part_Type_For_Set_Type(CreateView):

	model = Parts_Types

class Create_Set(CreateView):

	model = Set

class Put_Set_Into_Topic(CreateView):

	model = Sets

class Create_Part(CreateView):

	model = Part

class Create_Element(CreateView):

	model = Element
	fields = ['abstract']

class Put_Part_Into_Element(CreateView):

	model = Parts

class Put_Element_Into_Set(CreateView):

	model = Elements

class Show_Details(DetailView):

	template_name_basic = 'dictionaries/details'
	extra_context = {}

	def get_template_names(self):
		self.template_name = '{}/{}'.format(self.template_name_basic, self.template_name)
		return super().get_template_names()

	def get_queryset(self, *args, **kwargs):
		self.extra_context['object'] = self.model.objects.get(pk=self.kwargs['pk'])
		self.extra_context['model_name'] = self.model.__name__.capitalize()
		return super().get_queryset()

class UpdateView(UpdateView):

	model = None
	fields = ['title', 'abstract', 'language']
	disabled_fields = ['type']
	template_name_basic = 'dictionaries/update_forms'
	template_name = 'update_template_form.html'
	back_name = None
	message = None

	def get_template_names(self):
		self.template_name = '{}/{}'.format(self.template_name_basic, self.template_name)
		return super().get_template_names()

	def get_handled_model_name(self):
		return self.model.__name__.replace('_', ' ')

	def get_back_url(self):
		return reverse(self.model.list_namepath)

	def get_back_name(self):
		return self.back_name

	def create_extra_content(self):
		self.extra_context = {}
		self.extra_context["model_name"] = self.get_handled_model_name()
		self.extra_context["message"] = self.message
		self.extra_context["back_name"] = self.get_back_name()

	def get_form(self, form_class=None):
		form = super().get_form(form_class)
		for field in self.disabled_fields:
			if field in form.fields:
				form.fields[field].disabled = True
		return form

	def get(self, request, *args, **kwargs):
		self.object = self.get_object()
		self.create_extra_content()
		return super(BaseUpdateView, self).get(request, *args, **kwargs)

class Update_With_Created_DateTime_View(UpdateView):

	def create_extra_content(self):
		result = super().create_extra_content()
		self.extra_context["created_at"] = self.object.created_at
		return result

class Update_Subject(Update_With_Created_DateTime_View):

	model = Subject

	def get_back_name(self):
		return self.model.__name__ + 's'

class Update_Topic(Update_With_Created_DateTime_View):

	model = Topic

class Update_Set(Update_With_Created_DateTime_View):

	model = Set
	fields = ['title', 'type', 'abstract']
	template_name = 'update_set_template.html'

class Update_Element(Update_With_Created_DateTime_View):

	model = Element
	fields = ['type', 'abstract']

class Update_Part(UpdateView):

	model = Part
	fields = ['content', 'type', 'comment', 'style']
	template_name = 'update_part_template.html'

class Update_Playlist(Update_With_Created_DateTime_View):

	model = Playlist

	def get_back_name(self):
		return self.model.__name__ + 's'

class Show_Content_List(ListView):

	model = None
	container_model = None
	template_name = None
	extra_context = {}
	template_name_basic = 'dictionaries/content_lists'
	add_content_items = True

	def get_template_names(self):
		self.template_name = '{}/{}'.format(self.template_name_basic, self.template_name)
		return super().get_template_names()

	def get_content_name(self):
		return self.model.__name__.capitalize()

	def get_queryset(self, *args, **kwargs):
		self.extra_context = {}
		self.container_model = self.model.get_container_model()
		container_model_name = self.model.container_field_name
		self.extra_context["container_name"] = container_model_name.capitalize()
		self.extra_context["content_name"] = self.get_content_name()
		self.extra_context["content_field_name"] = self.model.content_field_name
		self.extra_context["change_position_url"] = self.model.change_position_url
		self.container = self.container_model.objects.get(id=self.kwargs[container_model_name])
		self.extra_context["container"] = self.container
		self.extra_context["container_id"] = self.container.id
		if self.model.container_container_model:
			self.extra_context["container_container_name"] = self.model.container_container_model.__name__ + 's'
		if self.add_content_items:
			model = self.model()
			model.set_container(self.container)
			self.extra_context["add_new_item_into_end_url"] = model.get_add_new_item_into_end_url()
		return super().get_queryset().filter(**{container_model_name: self.kwargs[container_model_name]}).order_by('position')

class Show_Subjects_List(Show_Content_List):

	model = Subject
	template_name = 'subjects_list.html'
	show_storage = False

	def get_queryset(self, *args, **kwargs):
		self.extra_context = {}
		self.extra_context["container_name"] = self.model.__name__ + 's'
		self.extra_context["content_field_name"] = self.model.__name__
		self.extra_context["change_position_url"] = self.model.change_position_url
		self.extra_context["add_new_item_into_end_url"] = self.model.get_add_new_item_into_end_url(self.show_storage)
		return super(ListView, self).get_queryset().order_by('position').filter(storage=self.show_storage)

class Show_Storage_Subjects_List(Show_Subjects_List):

	show_storage = True

	def get_queryset(self, *args, **kwargs):
		queryset = super().get_queryset()
		self.extra_context["container_name"] = 'Storage {}s '.format(self.model.__name__)
		return queryset

class Show_Subject_Topics_List(Show_Content_List):

	model = Topics
	template_name = "subject_topics_list.html"

class Show_Topic_Sets_List(Show_Content_List):

	model = Sets
	template_name = "topic_sets_list.html"

class Show_Set_Elements_List(Show_Content_List):

	model = Elements
	template_name = "set_elements_list.html"

	def get_queryset(self, *args, **kwargs):
		result = super().get_queryset()
		self.extra_context["parts_types"] = Parts_Types.objects.filter(set_type=self.container.type)
		return result

class Show_Element_Parts_List(Show_Content_List):

	model = Parts
	template_name = 'element_parts_list.html'
	add_content_items = False

class Show_Playlists_List(Show_Content_List):

	model = Playlist
	template_name = 'playlists_list.html'

	def get_queryset(self, *args, **kwargs):
		self.extra_context = {}
		self.extra_context["container_name"] = self.model.__name__ + 's'
		self.extra_context["content_field_name"] = self.model.__name__
		self.extra_context["change_position_url"] = self.model.change_position_url
		self.extra_context["add_new_item_into_end_url"] = self.model.get_add_new_item_into_end_url()
		return super(ListView, self).get_queryset().order_by('position')

class Show_Playlist_Sets_List(Show_Content_List):

	model = Sets_In_Playlists
	template_name = 'playlist_sets_list.html'
	add_content_items = True

	def get_content_name(self):
		return self.model.__name__.split('_')[0].capitalize()

class Show_Containers_List(ListView):

	extra_context = {}
	template_name_basic = 'dictionaries/containers_lists'
	template_name = 'containers_list.html'

	def get_template_names(self):
		self.template_name = '{}/{}'.format(self.template_name_basic, self.template_name)
		return super().get_template_names()

	def get_queryset(self, *args, **kwargs):
		self.extra_context = {}
		self.extra_context["content_name"] = self.model.content_field_name
		self.extra_context["container_name"] = self.model.container_field_name
		self.extra_context["content_object"] = self.model.get_content_model().objects.get(id=self.kwargs['pk'])
		return super().get_queryset().filter(**{self.model.content_field_name: self.kwargs['pk']}).order_by('position')

class Show_Topic_Subjects_List(Show_Containers_List):

	model = Topics

class Show_Set_Topics_List(Show_Containers_List):

	model = Sets

class Show_Element_Sets_List(Show_Containers_List):

	model = Elements

class Show_Part_Elements_List(Show_Containers_List):

	model = Parts

def correct_part(request, pk):
	part = Part.objects.prefetch_related('type').get(id=pk)
	if part.type_format == 'text':
		return render(request,
					"correct_element_text_part_template.html",
					{'part': part})

def correct_element_parts(request, element, part_position, part_direction, set=False, element_direction=False):
	template_variables_dict = {}
	if set:
		template_variables_dict["set_title"] = Set.objects.get(id=set).title
		template_variables_dict["set_id"] = set
		element_queryset_base = Elements.objects.filter(set=set)
		if element_direction == 'base':
			element = element_queryset_base.get(position=element)
		else:
			set_elements = element_queryset_base
			if element_direction == 'next':
				greater_elements = set_elements.filter(position__gt=element).order_by('position')
				element = greater_elements[0] if greater_elements.count() > 0 else set_elements[0]
			elif element_direction == 'previous':
				lower_elements = set_elements.filter(position__lt=element).order_by('-position')
				element = lower_elements[0] if lower_elements.count() > 0 else set_elements.order_by('-position')[0]
			elif element_direction == 'home':
				element = set_elements.order_by('position')[0]
			elif element_direction == 'end':
				element = set_elements.order_by('-position')[0]

		element_id = element.element
		element = element.position
		template_variables_dict["element_id"] = element_id.id
	else:
		element_id = element

	part_queryset_base = Parts.objects.filter(element=element_id)
	if part_direction == "base":
		part_in_element = part_queryset_base.prefetch_related('part').get(position=part_position)
	else:
		element_parts = part_queryset_base
		if part_direction == "next":
			greater_elements = element_parts.filter(position__gt=part_position).order_by('position')
			part_in_element = greater_elements[0] if greater_elements.count() > 0 else element_parts[0]
		elif part_direction == "previous":
			lower_elements = element_parts.filter(position__lt=part_position).order_by('-position')
			part_in_element = lower_elements[0] if lower_elements.count() > 0 else element_parts.order_by('-position')[0]

	template_variables_dict["element"] = element
	template_variables_dict["part"] = part_in_element.part
	template_variables_dict["part_position"] = part_in_element.position

	if part_in_element.part.type_format == 'text':
		template_name = "correct_element_text_part_template.html"
	elif part_in_element.part.type_format == 'url':
		template_name = "correct_element_text_part_template.html" # change to simple text form

	return render(request,
					template_name,
					template_variables_dict)

def save_corrected_text_part(request, pk):
	try:
		part = Part.objects.get(id=pk)
	except:
		response_text = "Can't find a part with ID {}".format(pk)
	else:
		try:
			body = request.body.decode("utf-8")
			input_dict = json.loads(body)
		except:
			response_text = "Wrong message format. Part can't be saved"
		else:
			if "string" in input_dict:
				part.content = input_dict["string"]

			styles_dict = {}
			styles_keys = ["main_color", "background_color", "letters_colors", "decorations"]
			for style_key in styles_keys:
				if style_key in input_dict:
					styles_dict[style_key] = input_dict[style_key]
			
			if len(styles_dict) > 0:
				part.style = json.dumps(styles_dict)
			else:
				part.style = None

			if "string" in input_dict or len(styles_keys) > 0:
				part.save()
				response_text = "Part has been saved "
			else:
				response_text = "Wrong message format. Part hasn't been saved"

	return JsonResponse({"response": response_text})

def clean_parts(request):
	parts = Part.objects.all()
	for part in parts:
		if part.content[-1] == ' ':
			part.content = part.content[:-1]
			part.save()
	return HttpResponseRedirect('/put_set_into_topic/')

class Change_Item_Position(View):
	model = None

	def get(self, *args, **kwargs):
		return HttpResponseRedirect(self.model.change_position(*args, **kwargs))

class Change_Subject_Position(Change_Item_Position):

	model = Subject

class Change_Topics_Position(Change_Item_Position):

	model = Topics

class Change_Sets_Position(Change_Item_Position):

	model = Sets

class Change_Elements_Position(Change_Item_Position):

	model = Elements

class Change_Playlist_Position(Change_Item_Position):

	model = Playlist

class Change_Playlist_Sets_Position(Change_Item_Position):

	model = Sets_In_Playlists

class Add_Item(CreateView):

	model = None
	template_name = 'create_form_template.html'
	fields = '__all__'

	def get_back_url(self):
		return reverse(self.model.list_namepath)

	def get_handled_name(self, name):
		return name.replace('_', ' ')

	def get_handled_model_name(self):
		return self.get_handled_name(self.model.__name__)

	def get_content_model_name(self, model_name):
		return 'Dictionaries\' {}s'.format(model_name)

	def get(self, request, *args, **kwargs):
		self.extra_context = {}
		model_name = self.get_handled_model_name()
		self.extra_context['content_model_name'] = model_name
		self.extra_context['container_model_name'] = self.get_content_model_name(model_name)
		self.extra_context['back_container_url'] = self.get_back_url()
		return super(CreateView, self).get(request, *args, **kwargs)

	def form_valid(self, form):
		form.save()
		return HttpResponseRedirect(self.get_back_url())

class Add_Content_Item_Into_Container(Add_Item):

	model = None
	template_name = 'create_form_template.html'
	fields = '__all__'

	def create_container_object(self):
		self.container_object = self.container_model.objects.get(id=self.kwargs['container'])

	def get_back_url(self):
		return self.container_object.get_content_list_url()

	def get(self, request, *args, **kwargs):
		self.extra_context = {}
		self.extra_context['content_model_name'] = self.get_handled_model_name()
		self.extra_context['container_model_name'] = self.get_handled_name(self.container_model.__name__)
		self.create_container_object()
		self.extra_context['container'] = self.container_object
		self.extra_context['back_container_url'] = self.get_back_url()
		return super(CreateView, self).get(request, *args, **kwargs)

	def form_valid(self, form):
		container_id = self.kwargs['container']
		self.create_container_object()
		self.object = form.save()

		container_field_name = self.list_model.container_field_name
		content_field_name = self.list_model.content_field_name

		items_total = self.list_model.objects.filter(**{container_field_name: container_id}).count()
		list_object = self.list_model()
		list_object.set_container(self.container_object)
		list_object.set_content(self.object)
		list_object.position = items_total + 1
		list_object.save()

		self.list_model.change_position(container=container_id,
										position=list_object.position,
										direction=self.kwargs['direction'])

		redirect_url = list_object.get_absolute_url()
		return HttpResponseRedirect(redirect_url)

class Add_New_Subject(Add_Item):

	model = Subject
	fields = ('title', 'abstract', 'language')

	def get_back_url(self):
		return self.model.define_list_url(self.model.define_storage(self.define_subject_type()))

	def define_subject_type(self):
		return self.kwargs['container'] # active / storage

	def get_content_model_name(self, model_name):
		return 'Dictionaries\' {} {}s'.format(self.define_subject_type().capitalize(), model_name)

	def form_valid(self, form):
		subject_type = self.define_subject_type()
		subjects_total = self.model.get_items(subject_type).count()
		form.instance.position = subjects_total + 1
		form.instance.storage = self.model.define_storage(subject_type)
		self.object = form.save()
		self.model.change_position(container=self.kwargs['container'],
									position=self.object.position,
									direction=self.kwargs['direction'])
		return HttpResponseRedirect(self.object.get_list_url())

class Add_New_Topic_Into_Subject(Add_Content_Item_Into_Container):

	model = Topic
	list_model = Topics
	fields = ['title', 'abstract', 'language']
	container_model = Subject

class Add_New_Set_Into_Topic(Add_Content_Item_Into_Container):

	model = Set
	list_model = Sets
	fields = ['title', 'type', 'abstract', 'notes_available']
	container_model = Topic

def add_new_element_into_set(request, container, direction):

	url = Set.add_new_element(container, direction)
	return HttpResponseRedirect(url)

class Add_New_Playlist(Add_Item):

	model = Playlist
	fields = ('title', 'abstract', 'language')

	def get_back_url(self):
		return self.model.get_list_url()

	def form_valid(self, form):
		subjects_total = self.model.get_items().count()
		form.instance.position = subjects_total + 1
		self.object = form.save()
		self.model.change_position(position=self.object.position,
									direction=self.kwargs['direction'])
		return HttpResponseRedirect(self.object.get_list_url())

class DeleteView(DeleteView):

	model = None
	template_name_basic = "dictionaries/delete_forms"
	template_name = "delete_check_form.html"

	def get_template_names(self):
		self.template_name = '{}/{}'.format(self.template_name_basic, self.template_name)
		return super().get_template_names()

	def get_handled_name(self, name):
		return name.replace('_', ' ')

	def get_handled_model_name(self):
		return self.get_handled_name(self.model.__name__)

	def get_object(self, *args, **kwargs):
		self.extra_context = {}
		self.extra_context["content_model_name"] = self.get_handled_model_name()
		return super().get_object()

	def post(self, request, *args, **kwargs):
		object = self.model.objects.get(id=kwargs['pk'])
		return HttpResponseRedirect(object.delete())

class Delete_List_Item_View(DeleteView):

	model = None
	template_name = "delete_item_check_form.html"

	def get_container_model_name(self):
		return self.get_handled_name(self.model.container_field_name.capitalize())

	def get_object(self, *args, **kwargs):
		self.object = super().get_object()
		self.extra_context["container_model_name"] = self.get_container_model_name()
		self.extra_context["container"] = self.object.container
		return self.object

	def post(self, request, *args, **kwargs):
		return HttpResponseRedirect(self.model.delete_item(*args, **kwargs))

class Delete_Subject(Delete_List_Item_View):

	model = Subject

	def get_container_model_name(self):
		return '{} {}s'.format(self.get_handled_model_name(), self.object.get_container_title().capitalize())

class Delete_Subject_Topic(Delete_List_Item_View):

	model = Topics

class Delete_Topic_Set(Delete_List_Item_View):

	model = Sets
	template_name = "topic_set_check_delete_form.html"

class Delete_Set_Element(Delete_List_Item_View):

	model = Elements
	template_name = "set_element_check_delete_form.html"

class Delete_Set(DeleteView):

	model = Set
	template_name = "set_check_delete_form.html"

	def post(self, request, *args, **kwargs):
		set = self.get_object()
		return HttpResponseRedirect(set.delete_out_of_all_topics())

class Delete_Playlist(Delete_List_Item_View):

	model = Playlist

	def get_container_model_name(self):
		return '{}s'.format(self.get_handled_model_name())

class Delete_Playlist_Set(Delete_List_Item_View):

	model = Sets_In_Playlists

class Insert_Item(TemplateView):
	# https://github.com/django/django/blob/292b3be698ef58aff9c215d62a444f66ead578c3/django/views/generic/base.py#L16
	model = None
	container_model = None
	template_name_basic = 'dictionaries/insert_forms'
	template_name = 'insert_form.html'

	def get_template_names(self):
		self.template_name = '{}/{}'.format(self.template_name_basic, self.template_name)
		return super().get_template_names()

	def get(self, request, *args, **kwargs):
		object_id = kwargs["pk"]
		self.extra_context = {}
		self.extra_context["object"] = self.model.get_container_model().objects.get(id=object_id)
		self.extra_context["subjects"] = Subject
		self.extra_context["model"] = self.model
		return super().get(request, *args, **kwargs)

	def post(self, request, *args, **kwargs):
		kwargs['to_delete'] = request.POST.get("remove_from_source")
		kwargs['content_items_ids_to_insert'] = request.POST.getlist(self.model.content_field_name)
		return HttpResponseRedirect(self.model.insert_item(*args, **kwargs))

class Insert_Topic_Into_Subject(Insert_Item):

	model = Topics
	container_model = Subject

class Insert_Set_Into_Topic(Insert_Item):

	model = Sets
	container_model = Topic

class Insert_Element_Into_Set(Insert_Item):

	model = Elements
	container_model = Set
	template_name = 'insert_element_into_set_template.html'

	def get(self, request, *args, **kwargs):
		self.extra_context = {}
		set_id = kwargs["pk"]
		set = self.container_model.objects.prefetch_related('type').get(id=set_id)
		sets = Set.objects.filter(type=set.type).order_by('-created_at')
		self.extra_context["object"] = set
		self.extra_context["sets"] = sets
		context = self.get_context_data(**kwargs)
		return self.render_to_response(context)

	def post(self, request, *args, **kwargs):
		set_id = kwargs["pk"]
		elements_in_set = Elements.objects.filter(set=set_id).count()
		elements_positions = request.POST.getlist("element")
		source_set = request.POST.get("set")
		to_delete = request.POST.get("remove_from_source")
		destination_set = Set.objects.get(id=set_id)

		elements = Elements.objects.filter(set_id=source_set, position__in=elements_positions)
		for element in elements:
			elements_in_set += 1
			inserted_element_in_set = Elements(element=element.element,
												set_id=set_id,
												position = elements_in_set)
			inserted_element_in_set.save()
			if to_delete:
				self.model.delete_item(pk=element.id)
		return HttpResponseRedirect(destination_set.get_content_list_url())

class Insert_Set_Into_Playlist(Insert_Item):

	model = Sets_In_Playlists
	container_model = Playlist

	def post(self, request, *args, **kwargs):
		kwargs['to_delete'] = False
		kwargs['content_items_ids_to_insert'] = request.POST.getlist(self.model.content_field_name)
		kwargs['source_container_model'] = Sets
		return HttpResponseRedirect(self.model.insert_item(*args, **kwargs))

def activate_subject(request, pk):
	return HttpResponseRedirect(Subject.activate(pk))

class Show_Set_Types(ListView):

	model = Set_Type
	template_name_basic = 'dictionaries/sets_types_templates'
	template_name = 'sets_types_list.html'

	def get_template_names(self):
		self.template_name = '{}/{}'.format(self.template_name_basic, self.template_name)
		return super().get_template_names()

	def get_queryset(self, *args, **kwargs):
		self.extra_context = {}
		self.extra_context["container_name"] = 'Sets Types'
		self.extra_context["add_new_item_into_end_url"] = self.model.get_add_new_item_into_end_url()
		return super().get_queryset().order_by('name')

class Delete_Set_Type(DeleteView):

	model = Set_Type

class Add_New_Set_Type(Add_Item):

	model = Set_Type

	def form_valid(self, form):
		self.object = form.save()
		return HttpResponseRedirect(self.object.get_absolute_url())

class Update_Set_Type(UpdateView):

	model = Set_Type
	fields = ('name', 'language', 'abstract')
	template_name_basic = 'dictionaries/sets_types_templates'
	template_name = 'set_type_update_form.html'
	back_name = 'Sets Types'

	def form_valid(self, form):
		storage_set = Set.get_storage_set_for_type(self.model.objects.get(pk=self.kwargs['pk']))
		new_storage_set_title = Set.get_storage_title_for_type(form.instance.name)
		if storage_set.title != new_storage_set_title:
			storage_set.title = new_storage_set_title
			storage_set.save()
		return super().form_valid(form)

class Change_Part_Type_Position(Change_Item_Position):

	model = Parts_Types

class Add_New_Part_Type_Into_Set_Type(Add_Content_Item_Into_Container):

	model =	Parts_Types
	list_model = Parts_Types
	fields = ['type']
	container_model = Set_Type
	template_name = 'dictionaries/add_items_templates/add_new_part_type_into_set_type_template.html'

	def form_valid(self, form):
		container_id = self.kwargs['container']
		container_field_name = self.list_model.container_field_name
		form.instance.set_type = self.container_model.objects.get(pk=container_id)
		items_total = self.list_model.objects.filter(**{container_field_name: container_id}).count()
		form.instance.position = items_total + 1
		object = form.save()
		object.add_part_with_part_type_into_elements()
		redirect_url = object.container.get_absolute_url()
		return HttpResponseRedirect(redirect_url)

class Delete_Part_Type_Out_Of_Set_Type(Delete_List_Item_View):

	model = Parts_Types
	template_name = "set_type_part_type_delete_form.html"

class Show_Sets_For_Set_Types(Show_Containers_List):

	model = Set
	template_name = 'sets_for_set_type.html'

	def get_queryset(self, *args, **kwargs):
		self.extra_context = {}
		container_field_name = 'set'
		content_field_name = 'set type'
		self.extra_context["content_name"] = content_field_name
		self.extra_context["container_name"] = container_field_name
		self.extra_context["content_object"] = Set_Type.objects.get(id=self.kwargs['pk'])
		return self.model.objects.filter(**{'type': self.kwargs['pk']}).order_by('created_at')

class Show_Parts_Types(ListView):

	model = Part_Type
	template_name_basic = 'dictionaries/parts_types_templates'
	template_name = 'parts_types_list.html'

	def get_template_names(self):
		self.template_name = '{}/{}'.format(self.template_name_basic, self.template_name)
		return super().get_template_names()

	def get_queryset(self, *args, **kwargs):
		self.extra_context = {}
		self.extra_context["container_name"] = 'Parts Types'
		self.extra_context["add_new_item_into_end_url"] = Part_Type.get_add_new_item_into_end_url()
		Part_Format.ensure_part_formats_existence()
		return super().get_queryset().order_by('language')

class Update_Part_Type(UpdateView):

	model = Part_Type
	fields = ['name', 'format', 'language']
	back_name = "Parts Types"
	message = "Changing part type's propeties changes proper parts' propeties in related sets!"

class Add_New_Part_Type(Add_Item):

	model = Part_Type

class Delete_Part_Type(DeleteView):

	model = Part_Type

class Show_Languages(ListView):

	model = Language
	template_name_basic = 'dictionaries/languages_templates'
	template_name = 'languages_list.html'

	def get_template_names(self):
		self.template_name = '{}/{}'.format(self.template_name_basic, self.template_name)
		return super().get_template_names()

	def get_queryset(self, *args, **kwargs):
		self.extra_context = {}
		self.extra_context["container_name"] = self.model.__name__ + 's'
		self.extra_context["add_new_item_into_end_url"] = self.model.get_add_new_item_into_end_url()
		self.model.ensure_languages_existence()
		return super().get_queryset().order_by('english_name')

class Update_Language(UpdateView):

	model = Language
	fields = '__all__'
	disabled_fields = ['code']
	back_name = "Languages"
	message = "Can be only one default language"

	def get_form(self, form_class=None):
		form = super().get_form(form_class)
		form.fields['original_name'].required = False
		form.fields['translation_name'].required = False
		return form

	def form_valid(self, form):
		form.instance.code = form.instance.english_name
		current_language = self.get_object()
		if current_language.english_name != form.instance.english_name:
			form.instance.original_name = ''
			form.instance.translation_name = ''
		self.model.insert_default_languages_names(form)
		default_languages = self.model.objects.filter(default=True)
		if form.instance.default:
			for default_language in default_languages:
				if default_language != self.object:
					default_language.default = False
					default_language.save()
		elif default_languages.count() == 0:
			default_language = self.model.get_default_language()
			default_language.default = True
			default_language.save()

		if not form.instance.code:
			form.instance.code = None

		return super().form_valid(form)

class Delete_Language(DeleteView):

	model = Language

class Add_New_Language(Add_Item):

	model = Language
	fields = ['original_name', 'english_name', 'translation_name', 'default']
	unrequired_fields = ['original_name', 'translation_name']

	def get_form(self, form_class=None):
		form = super().get_form(form_class)
		for field in self.unrequired_fields:
			if field in form.fields:
				form.fields[field].required = False
		return form

	def form_valid(self, form):
		if not self.model.language_with_english_name_exisits(form.instance.english_name):
			form.instance.code = form.instance.english_name
			self.model.insert_default_languages_names(form)
			object = form.save()
			return HttpResponseRedirect(object.get_absolute_url())
		else:
			return HttpResponseRedirect(self.get_back_url())

def show_start_page(request):
	return render(request,
				"start_page_template.html",
				{"links_list": [('Show subjects', reverse('show_subjects')),
								('Import Set', reverse('import_set')),
								('Create Subject', reverse('create_subject')),
								('Create Topic', reverse('create_topic')),
								('Put Topic into Subject', reverse('put_topic_into_subject')),

								('Set Part Type for Set Type', reverse('set_part_type_for_set_type')),
								('Create Set Type', reverse('create_set_type')),
								('Create Set', reverse('create_set')),
								('Put Set into Topic', reverse('put_set_into_topic')),
				]})

class User_Profile(CreateView):

	model = User

	def get(self, request, *args, **kwargs):
		users = self.model.objects.all()
		if users.count() > 0:
			return Update_User.as_view()(request=request, pk=users[0].id)
		else:
			return super().get(request, *args, **kwargs)

	def post(self, request, *args, **kwargs):
		users = self.model.objects.all()
		if users.count() > 0:
			return Update_User.as_view()(request=request, pk=users[0].id)
		else:
			return super().post(request, *args, **kwargs)

class Update_User(UpdateView):

	model = User
	fields = '__all__'
	disabled_fields = ['timezone']
	template_name_basic = 'dictionaries/user_templates'
	template_name = 'update_user_form.html'
	back_name = None
	message = 'Changing of language changes translated names for all languages'

	def create_extra_content(self):
		result = super().create_extra_content()
		self.extra_context["assign_timezone"] = reverse('assign_timezone')
		return result

	def form_valid(self, form):
		self.model.ensure_languages_translation(form)
		return HttpResponseRedirect(reverse('user_profile'))

def assign_timezone(request):
	if request.method == 'POST':
		timezone = request.POST.get('timezone')
		if timezone:
			request.session['django_timezone'] = timezone
			User.save_timezone(timezone)
		return redirect(reverse('user_profile'))
	else:
		return render(request,
					'dictionaries/user_templates/timezone_template.html',
					{'timezones': pytz.common_timezones})

def save_comment(request):
	try:
		body = request.body.decode("utf-8")
		input_dict = json.loads(body)
	except:
		response_text = "Wrong message format. Can't be saved"
	else:
		id = input_dict["id"]
		type = input_dict["type"]
		text = input_dict["text"]

		models = {'element': Element,
					"part": Part}
		response_text = models[type].save_text_abstract(id, text)

	return JsonResponse({"response": response_text})

def save_item_color(request):
	try:
		body = request.body.decode("utf-8")
		input_dict = json.loads(body)
	except:
		response_text = "Wrong message format. Color can't be saved"
	else:
		id = input_dict["id"]
		type = input_dict["type"]
		color = input_dict["color"]

		models = {"subject": Subject,
					"topic": Topic,
					"set": Set,
					"playlist": Playlist}
		response_text = models[type].save_color(id, color)

	return JsonResponse({"response": response_text})

def save_part_type_color(request):
	try:
		body = request.body.decode("utf-8")
		input_dict = json.loads(body)
	except:
		response_text = "Wrong message format. Color can't be saved"
	else:
		response_text = Parts_Types.save_color(input_dict)
		return JsonResponse({"response": response_text})

def change_set_notes_availability(request, id):
	response_text = Set.change_notes_availability(id)
	return JsonResponse({"response": response_text})

def notes(request):
	if request.method == 'GET':
		sets = Set.objects.filter(notes_available=True)
		return render(request,
					'create_notes.html',
					{'sets': sets})
	else:
		try:
			body = request.body.decode("utf-8")
			input_dict = json.loads(body)
		except:
			response_text = "Wrong note format. Note can't be saved"
		else:
			response_text = Set.save_element_as_note(input_dict)
		return JsonResponse({"response": response_text})

def export_native_formated_set(request):
	return Set.generate_export_file('native', request)

def export_common_formated_set(request, set):
	if request.method == 'GET':
		form = Export_Common_Formated_Set_Form()
		return render(request,
				"dictionaries/export_templates/export_common_format_set_template.html",
				{"form": form,
				"set": Set.objects.get(id=set)})
	elif request.method == 'POST':
		return Set.generate_export_file('common', request)

def import_common_formated_set(request):

	def render_import_form(form):
		return render(request,
					"dictionaries/import_templates/import_common_formated_set_form_template.html",
					{"form": form,
					"subjects": Subject})

	if request.method == 'POST':
		form = Import_Common_Formated_Set_Form(request.POST)
		if form.is_valid():
			url = Set.import_common_formated_set(form)
			return HttpResponseRedirect(url)
		else:
			return render_import_form(form)

	elif request.method == 'GET':
		form = Import_Common_Formated_Set_Form()
		return render_import_form(form)

def import_native_formated_set(request):
	if request.method == 'GET':
		return render(request,
				"dictionaries/import_templates/import_native_formated_set_form_template.html",
				{"subjects": Subject})
	elif request.method == 'POST':
		topic = request.POST.get('topic')
		raw_set_dict = ''
		if request.FILES:
			for chunk in request.FILES['set_file'].chunks():
				raw_set_dict += chunk.decode()
		try:
			set_dict = json.loads(raw_set_dict)
		except:
			print('WRONG FORMAT')
			url = False
		else:
			topic = Topics.objects.get(id=topic).topic.id
			url = Set.import_native_formated_set(topic, set_dict)
		if not url:
			url = reverse('import_native_formated_set')
		return HttpResponseRedirect(url)