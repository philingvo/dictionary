from rest_framework import serializers, viewsets
from .models import *


class Language_serializer(serializers.ModelSerializer):

	class Meta:
		model = Language
		fields = ('__all__')

class Part_Type_serializer(serializers.ModelSerializer):

	class Meta:
		model = Part_Type
		fields = ('__all__')

class Part_serializer(serializers.ModelSerializer):

	class Meta:
		model = Part
		fields = ('__all__')

class Element_serializer(serializers.ModelSerializer):

	class Meta:
		model = Element
		fields = ('__all__')

class Subject_serializer(serializers.ModelSerializer):

	language = Language_serializer()

	class Meta:
		model = Subject
		fields = ('__all__')

class Topic_serializer(serializers.ModelSerializer):

	language = Language_serializer()

	class Meta:
		model = Topic
		fields = ('__all__')

class Topics_serializer(serializers.ModelSerializer):

	topic = Topic_serializer()

	class Meta:
		model = Topics
		fields = ('__all__')

class Set_Type_serializer(serializers.ModelSerializer):

	language = Language_serializer()

	class Meta:
		model = Set_Type
		fields = ('__all__')

class Part_Format_serializer(serializers.ModelSerializer):

	class Meta:
		model = Part_Format
		fields = ('__all__')

class Part_Type_serializer(serializers.ModelSerializer):

	format = Part_Format_serializer()
	language = Language_serializer()
	
	class Meta:
		model = Part_Type
		fields = ('__all__')

class Parts_Types_serializer(serializers.ModelSerializer):

	type = Part_Type_serializer()

	class Meta:
		model = Parts_Types
		exclude = ['set_type']

class Set_serializer(serializers.ModelSerializer):

	type = Set_Type_serializer()

	class Meta:
		model = Set
		fields = ('__all__')

class Sets_serializer(serializers.ModelSerializer):

	set = Set_serializer()
	
	class Meta:
		model = Sets
		fields = ('__all__')

class Sets_In_Playlist_serializer(serializers.ModelSerializer):

	set = Set_serializer()
	
	class Meta:
		model = Sets_In_Playlists
		fields = ('__all__')

class Parts_serializer(serializers.ModelSerializer):

	part = serializers.SerializerMethodField()

	class Meta:
		model = Parts
		exclude = ['element']

	def get_part(self, part_object):
		queryset = Part.objects.get(id=part_object.part.id)
		return Part_serializer(queryset).data

class Elements_serializer(serializers.ModelSerializer):

	parts = serializers.SerializerMethodField()

	class Meta:
		model = Elements
		fields = ('__all__')

	def get_parts(self, element_object):
		queryset = Parts.objects.filter(element=element_object.element.id).order_by('position')
		return Parts_serializer(queryset, many=True).data

class Playlist_serializer(serializers.ModelSerializer):

	language = Language_serializer()

	class Meta:
		model = Playlist
		fields = ('__all__')

class Language_Export_serializer(serializers.ModelSerializer):
	class Meta:
		model = Language
		exclude = ['id', 'original_name', 'english_name', 'translation_name', 'default']

class Set_Type_Export_serializer(serializers.ModelSerializer):

	language = Language_Export_serializer()

	class Meta:
		model = Set_Type
		fields = ('__all__')

class Set_Export_serializer(serializers.ModelSerializer):

	type = Set_Type_Export_serializer()

	class Meta:
		model = Set
		exclude = ['created_at', 'storage', 'notes_available', 'color']

class Part_Format_Export_serializer(serializers.ModelSerializer):
	class Meta:
		model = Part_Format
		exclude = ['id']

class Part_Type_Export_serializer(serializers.ModelSerializer):

	format = Part_Format_Export_serializer()
	language = Language_Export_serializer()

	class Meta:
		model = Part_Type
		exclude = ['id']

class Parts_Types_Export_serializer(serializers.ModelSerializer):

	type = Part_Type_Export_serializer()

	class Meta:
		model = Parts_Types
		exclude = ['id', 'set_type']

class Part_Export_serializer(serializers.ModelSerializer):

	class Meta:
		model = Part
		exclude = ['id', 'type']

class Parts_Export_serializer(serializers.ModelSerializer):

	part = serializers.SerializerMethodField()

	class Meta:
		model = Parts
		exclude = ['id', 'element']

	def get_part(self, part_object):
		queryset = Part.objects.get(id=part_object.part.id)
		return Part_Export_serializer(queryset).data

class Element_Export_serializer(serializers.ModelSerializer):
	class Meta:
		model = Element
		fields = ['abstract']

class Elements_Export_serializer(serializers.ModelSerializer):

	parts = serializers.SerializerMethodField()
	element = serializers.SerializerMethodField()

	class Meta:
		model = Elements
		exclude = ['id', 'set']

	def get_parts(self, element_object):
		queryset = Parts.objects.filter(element=element_object.element.id).order_by('position')
		return Parts_Export_serializer(queryset, many=True).data

	def get_element(self, part_object):
		queryset = Element.objects.get(id=part_object.element.id)
		return Element_Export_serializer(queryset).data