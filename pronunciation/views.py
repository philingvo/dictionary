from django.shortcuts import render
from dictionaries.views import DeleteView
from dictionaries.views import Add_Item
from django.views.generic.edit import UpdateView
from django.views.generic.list import ListView
from django.http import HttpResponseRedirect
from .models import Pronunciation
from .models import Pronunciation_File
from .forms import Add_Pronunciation_File_Form


def get_pronunciation_audio(request):
	return Pronunciation.give_pronunciation_file(request)

def get_pronunciation_local_filepath(request):
	return Pronunciation.give_pronunciation_local_filepath(request)

def show_pronunciation_page(request):
	if request.method == "GET":
		return Pronunciation.get_pronunciation_page(request)
	elif request.method == "POST":
		return Pronunciation.set_pronunciation_file(request)

def add_pronunciation_file(request, pk):
	if request.method == "GET":
		return Pronunciation.get_adding_pronunciation_file_page(request, pk)
	elif request.method == "POST":
		return Pronunciation_File.upload_file(request)

def get_pronunciation_files_list(request, pk):
	return Pronunciation.get_pronunciation_files_list(request, pk)

def play_file(request, pk):
	pronunciation_file = Pronunciation_File.objects.get(id=pk)
	return pronunciation_file.play_file()

def set_file_as_current(request, pk):
	pronunciation_file = Pronunciation_File.objects.get(id=pk)
	return pronunciation_file.set_file_as_current()

class Update_Basic(UpdateView):

	model = None
	template_name_basic = "pronunciation"
	template_name = "correct_form_template.html"
	fields = "__all__"
	disabled_fields = []
	excluded_fields = []

	def get_template_names(self):
		self.template_name = '{}/{}'.format(self.template_name_basic, self.template_name)
		return super().get_template_names()

	def get_form(self, form_class=None):
		form = super().get_form(form_class)
		if len(self.disabled_fields) > 0:
			form = self.disable_form_fields(form)
		if len(self.excluded_fields) > 0:
			form = self.exclude_form_fields(form)
		return form

	def disable_form_fields(self, form):
		for field in self.disabled_fields:
			if field in form.fields:
				form.fields[field].disabled = True
		return form

	def exclude_form_fields(self, form):
		for field in self.excluded_fields:
			if field in form.fields:
				del form.fields[field]
		return form

	def get(self, request, *args, **kwargs):
		self.extra_context = {"title": 'Correct {}'.format(self.model.__name__.replace("_", " ")),
								"object": self.get_object()}
		return super().get(request, *args, **kwargs)

class Update_Pronunciation(Update_Basic):

	model = Pronunciation
	template_name = "correct_pronunciation.html"
	disabled_fields = ["language"]

class Update_Pronunciation_File(Update_Basic):

	model = Pronunciation_File
	template_name = "correct_pronunciation_file.html"
	disabled_fields = ["pronunciation"]
	excluded_fields = ["filename", "choosen"]

class ListView(ListView):

	template_name_basic = "pronunciation"
	paginate_by = 5
	items_on_page_list = [5, 10, 15, 20, 25]
	ordering_field = "text"
	
	def get_template_names(self):
		self.template_name = '{}/{}'.format(self.template_name_basic, self.template_name)
		return super().get_template_names()

	def get_page_title(self):
		return self.model.__name__.replace("_", " ") + 's'

	def get_queryset(self):

		def create_querystring(querysting_dict, excluded_param_name):
			if len(querysting_dict) > 0:
				querysting = '&'
				for param_name, param_value in querysting_dict.items():
					if param_name != excluded_param_name:
						querysting = "{}{}={}&".format(querysting, param_name, param_value)
				return querysting
			else:
				return ""

		searching_param_name = "searching_text"
		order_param_name = "order"
		page_param_name = "page"
		paginate_by_param_name = "paginate_by"

		searching_param_value = self.request.GET.get(searching_param_name, None)
		order_param_value = self.request.GET.get(order_param_name, None)
		page_param_value = self.request.GET.get(page_param_name, "1")
		paginate_by = self.request.GET.get(paginate_by_param_name, str(self.paginate_by))
		self.paginate_by = int(paginate_by)

		querysting_dict = {}
		self.extra_context = {}
		self.extra_context["searching_param_name"] = searching_param_name
		self.extra_context["order_param_name"] = order_param_name
		self.extra_context["page_param_name"] = page_param_name
		self.extra_context["paginate_by_param_name"] = paginate_by_param_name

		if searching_param_value:
			queryset = self.model.search(searching_param_value)
			querysting_dict[searching_param_name] = searching_param_value
			self.extra_context["previous_searching_request"] = searching_param_value
		else:
			queryset = super().get_queryset()

		if order_param_value:
			ordering_field = self.ordering_field
			if order_param_value == "descending":
				ordering_field = "-" + ordering_field
			queryset = queryset.order_by(ordering_field)
			querysting_dict[order_param_name] = order_param_value
		else:
			queryset = queryset.order_by(self.ordering_field)

		if page_param_value and page_param_value.isdigit():
			page_param_value = int(page_param_value)
			querysting_dict[page_param_name] = page_param_value

		if paginate_by and paginate_by.isdigit():
			paginate_by = int(paginate_by)
			querysting_dict[paginate_by_param_name] = paginate_by

		pronunciations_count = queryset.count()
		if querysting_dict[page_param_name] * querysting_dict[paginate_by_param_name] > pronunciations_count:
			page_param_value = pronunciations_count // paginate_by
			if pronunciations_count % paginate_by > 0:
				page_param_value += 1
			self.request.GET._mutable = True
			querysting_dict[page_param_name] = self.request.GET[page_param_name] = page_param_value
		
		self.extra_context["page_querysting"] = create_querystring(querysting_dict, page_param_name)
		self.extra_context["order_querysting"] = create_querystring(querysting_dict, order_param_name)
		self.extra_context["paginate_querysting"] = create_querystring(querysting_dict, paginate_by_param_name)		
		self.extra_context["title"] = self.get_page_title()
		self.extra_context["items_on_page_list"] = self.items_on_page_list
		return queryset

# https://medium.com/@j.yanming/simple-search-page-with-pagination-in-django-154ad259f4d7
class Pronunciations_List(ListView):

	model = Pronunciation
	template_name = "pronunciations_list_template.html"

	def get_queryset(self):
		queryset = ListView.get_queryset(self)
		self.extra_context["url"] = self.model.get_add_new_pronunciation_url
		return queryset

class DeleteView(DeleteView):

	template_name_basic = "pronunciation"
	template_name = "delete_form_template.html"

	def get_delete_file_status(self, request):
		return request.POST.get("delete_file")

	def post(self, request, *args, **kwargs):
		object = self.model.objects.get(id=kwargs['pk'])
		delete_file = self.get_delete_file_status(request)
		return HttpResponseRedirect(object.delete(delete_file=delete_file))

class Delete_Pronunciation(DeleteView):

	model = Pronunciation

class Pronunciations_Files_List(ListView):

	model = Pronunciation_File
	ordering_field = "pronunciation__text"
	template_name = "pronunciations_files_list_template.html"

class Delete_Pronunciation_File(DeleteView):

	model = Pronunciation_File

class Add_New_Pronunciation(Add_Item):

	model = Pronunciation
	fields = '__all__'
	template_name = 'pronunciation/add_pronunciation_template.html'

	def form_valid(self, form):
		pronunciation = form.save()
		return HttpResponseRedirect(pronunciation.get_absolute_url())
