from django import forms
from django.forms import Form, ModelChoiceField, ModelForm, Textarea, CharField, TextInput, BooleanField, HiddenInput, IntegerField, SelectMultiple, MultipleChoiceField, FileField, ModelMultipleChoiceField, Select, ChoiceField
from .models import Set, Subject, Set_Type


class Import_Export_Set_Common_Format_Base_Form(Form):

	part_separators = [(";", ";"),
						("-", "-"),
						(",", ","),
						("tab", "CHARACTER TABULATION")]
	element_separators = [("\\n", "LINE FEED (\\n)"),
						(";", ";"),
						("tab", "CHARACTER TABULATION")]
	part_separator = CharField(required=True,
								widget=Select(choices=part_separators))
	element_separator = CharField(required=True,
								widget=Select(choices=element_separators))
	raw_text = CharField(widget=Textarea(attrs={'cols': 70, 'rows': 12}), # 'readonly': True
						required=True)

class Import_Common_Formated_Set_Form(ModelForm, Import_Export_Set_Common_Format_Base_Form):

	class Meta:
		model = Set
		exclude = ['created_at', 'storage', 'notes_available', 'color']
		widgets = {'title': TextInput(attrs={'size': 70}),
					'abstract': Textarea(attrs={'cols': 70, 'rows': 1})}

	type = ModelChoiceField(queryset=Set_Type.objects.order_by('language'))
	google_translate_formated = BooleanField(help_text="Exclude two first parts (languages)",
											required=False)

	def clean(self):
		
		def clean_separator(raw_separator):
			if raw_separator == '\\n':
				return '\n'
			elif raw_separator == 'tab':
				return '\t'
			else:
				return raw_separator

		def get_no_separator_error_text(separator_name):
			return 'No {} symbol in the importing text'.format(separator_name.upper())
		
		super().clean()
		raw_text = self.cleaned_data['raw_text']
		if raw_text:
			part_separator = self.cleaned_data['part_separator'] = clean_separator(self.cleaned_data['part_separator'])
			element_separator = self.cleaned_data['element_separator'] = clean_separator(self.cleaned_data['element_separator'])			
			
			if element_separator not in raw_text:
				self.add_error('element_separator',
								get_no_separator_error_text("string separator") + '. Must be at least 2 elements')
			if part_separator == element_separator:
				raise forms.ValidationError("Word separator and string separator can't be the same")
		else:
			raise forms.ValidationError("No text for set importing")

class Export_Common_Formated_Set_Form(Import_Export_Set_Common_Format_Base_Form):

	no_content_text = CharField(initial='No content')
	replace_separator_in_content = BooleanField(help_text="If any separator is in a content text, this separator will be replaced with '|'",
												initial=True)