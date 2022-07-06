from django.forms import ModelForm
from django.forms import IntegerField
from django.forms import FileField
from django.forms import HiddenInput
from django.forms import BooleanField
from django.forms import CheckboxInput
from django.forms import TextInput
from .models import Pronunciation_File


class Add_Pronunciation_File_Form(ModelForm):
	
	class Meta:
		model = Pronunciation_File
		fields = ["pronunciation",
					"source",
					"accent",
					]
		widgets = {'pronunciation': TextInput(attrs={'disabled': True})}

	uploadfile = FileField(required=True)
	choose = BooleanField(required=False,
						widget=CheckboxInput(
						attrs={'title': 'Choose as current'})
						)

	def is_valid(self, uploaded_file):
		if self.data["pronunciation"] and self.data["source"] and self.data["accent"] and str(uploaded_file).split(".")[-1] == "mp3":
			return True
		else:
			return False

	def save(self, pronunciation, filename):
		pronunciation_file = self.Meta.model(pronunciation=pronunciation,
										source=self.data["source"],
										accent=self.data["accent"],
										filename=filename)
		pronunciation_file.save()
		return pronunciation_file