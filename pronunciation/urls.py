from django.urls import path
from pronunciation.views import *

urlpatterns = [
	path('pronunciations_list/', Pronunciations_List.as_view(), name="pronunciations_list"),
	path('pronunciation_files_list/<int:pk>/', get_pronunciation_files_list, name="pronunciation_files_list"),
	path('pronunciation_page/', show_pronunciation_page, name="pronunciation_page"),
	path('correct_pronunciation/<int:pk>/', Update_Pronunciation.as_view(), name="correct_pronunciation"),
	path('add_new_pronunciation/', Add_New_Pronunciation.as_view(), name="add_new_pronunciation"),
	path('delete_pronunciation/<int:pk>/', Delete_Pronunciation.as_view(), name="delete_pronunciation"),
	path('pronunciations_files_list/', Pronunciations_Files_List.as_view(), name="pronunciations_files_list"),
	path('correct_pronunciation_file/<int:pk>/', Update_Pronunciation_File.as_view(), name="correct_pronunciation_file"),
	path('set_file_as_current/<int:pk>/', set_file_as_current, name="set_file_as_current"),
	path('add_pronunciation_file/<int:pk>/', add_pronunciation_file, name="add_pronunciation_file"),
	path('delete_pronunciation_file/<int:pk>/', Delete_Pronunciation_File.as_view(), name="delete_pronunciation_file"),
	path('pronounce/', get_pronunciation_audio, name="pronounce"),
	path('pronunciation_local_filepath/', get_pronunciation_local_filepath, name="pronunciation_local_filepath"),
	path('play_file/<int:pk>/', play_file, name='play_file'),
]