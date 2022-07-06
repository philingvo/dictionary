"""dictionary URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path, include
from rest_framework import routers
from dictionaries.views import *


router = routers.DefaultRouter()
router.register(r'subjects', Subjects_List_ViewSet, basename='subjects')
router.register(r'topics', Topics_List_ViewSet, basename='topics')
router.register(r'sets', Sets_List_ViewSet, basename='sets')
router.register(r'sets_by_topics_id', Sets_List_By_Topics_ID_ViewSet, basename='sets_by_topics_id')
router.register(r'set', Set_ViewSet, basename='set')
router.register(r'sets_the_same_type', Sets_List_For_The_Same_Set_Type_ViewSet, basename='sets_the_same_type')
router.register(r'elements', Elements_List_ViewSet, basename='elements')
router.register(r'parts', Parts_List_ViewSet, basename='parts')
router.register(r'part', Part_ViewSet, basename='part')
router.register(r'set_with_elements', Set_With_Elements_ViewSet, basename='set_with_elements')
router.register(r'set_length', Set_Length_ViewSet, basename='set_length')
router.register(r'set_with_elements_from_queue', Set_With_Elements_From_Queue_ViewSet, basename='set_with_elements_from_queue')
router.register(r'part_types', Set_With_Part_Types_ViewSet, basename='part_types')
router.register(r'playlist_set_with_elements_from_queue', Playlist_Set_With_Elements_From_Queue_ViewSet, basename='playlist_set_with_elements_from_queue')
router.register(r'playlists', Playlists_List_ViewSet, basename='playlists')
router.register(r'sets_in_playlist', Sets_In_Playlist_List_ViewSet, basename='sets_in_playlist')
urlpatterns = [
    path('admin/', admin.site.urls),
    path(r'api/', include(router.urls)),

    path(r'create_subject/', Create_Subject.as_view(), name='create_subject'),
    path(r'create_topic/', Create_Topic.as_view(), name='create_topic'),
    path(r'create_set_type/', Create_Set_Type.as_view(), name='create_set_type'),
    path(r'create_part_format/', Create_Part_Format.as_view(), name='create_part_format'),
    path(r'create_part_type/', Create_Part_Type.as_view(), name='create_part_type'),
    path(r'set_part_type_for_set_type/', Set_Part_Type_For_Set_Type.as_view(), name='set_part_type_for_set_type'),
    path(r'create_set/', Create_Set.as_view(), name='create_set'),
    path(r'create_element/', Create_Element.as_view(), name='create_element'),
    
    path(r'put_topic_into_subject/', Put_Topic_Into_Subject.as_view(), name='put_topic_into_subject'),
    path(r'put_set_into_topic/', Put_Set_Into_Topic.as_view(), name='put_set_into_topic'),
    path(r'put_element_into_set/', Put_Element_Into_Set.as_view(), name='put_element_into_set'),
    path(r'put_part_into_element/', Put_Part_Into_Element.as_view(), name='put_part_into_element'),

    path('show_subject/<int:pk>/', Update_Subject.as_view(), name='show_subject'),
    path('show_topic/<int:pk>/', Update_Topic.as_view(), name='show_topic'),
    path('show_set/<int:pk>/', Update_Set.as_view(), name='show_set'),
    path('show_element/<int:pk>/', Update_Element.as_view(), name='show_element'),
    path('show_part/<int:pk>/', Update_Part.as_view(), name='show_part'),
    path('show_playlist/<int:pk>/', Update_Playlist.as_view(), name='show_playlist'),
	
	path('show_subjects/', Show_Subjects_List.as_view(), name='show_subjects'),
    path('show_storage_subjects/', Show_Storage_Subjects_List.as_view(), name='show_storage_subjects'),
    path('show_subject_topics/<int:subject>/', Show_Subject_Topics_List.as_view(), name='show_subject_topics'),
    path('show_topic_sets/<int:topic>/', Show_Topic_Sets_List.as_view(), name='show_topic_sets'),
    path('show_set_elements/<int:set>/', Show_Set_Elements_List.as_view(), name='show_set_elements'),
    path('show_element_parts/<int:element>/', Show_Element_Parts_List.as_view(), name='show_element_parts'),
    path('show_playlists/', Show_Playlists_List.as_view(), name='show_playlists'),
    path('show_playlist_sets/<int:playlist>/', Show_Playlist_Sets_List.as_view(), name='show_playlist_sets'),
    
    path('show_topic_subjects/<int:pk>/', Show_Topic_Subjects_List.as_view(), name='show_topic_subjects'),
    path('show_set_topics/<int:pk>/', Show_Set_Topics_List.as_view(), name='show_set_topics'),
    path('show_element_sets/<int:pk>/', Show_Element_Sets_List.as_view(), name='show_element_sets'),
    path('show_part_elements/<int:pk>/', Show_Part_Elements_List.as_view(), name='show_part_elements'),

    path('correct_part/<int:pk>/', correct_part, name='correct_part'),
    path('save_corrected_text_part/<int:pk>/', save_corrected_text_part, name='save_corrected_text_part'),

    path('correct_element_parts/<int:element>/<int:part_position>/<str:part_direction>/', correct_element_parts, name='correct_element_parts'),
    path('correct_set_element_parts/<int:element>/<int:part_position>/<str:part_direction>/<int:set>/<str:element_direction>/', correct_element_parts, name='correct_set_element_parts'),

    path('change_subject_position/<str:container>/<int:position>/<str:direction>/', Change_Subject_Position.as_view(), name='change_subject_position'),
    path('change_topics_position/<int:container>/<int:position>/<str:direction>/', Change_Topics_Position.as_view(), name='change_topics_position'),
    path('change_sets_position/<int:container>/<int:position>/<str:direction>/', Change_Sets_Position.as_view(), name='change_sets_position'),
    path('change_elements_position/<int:container>/<int:position>/<str:direction>/', Change_Elements_Position.as_view(), name='change_elements_position'),
    path('change_playlist_position/<int:position>/<str:direction>/', Change_Playlist_Position.as_view(), name='change_playlist_position'),
    path('change_playlist_sets_position/<int:container>/<int:position>/<str:direction>/', Change_Playlist_Sets_Position.as_view(), name='change_playlist_sets_position'),

    path('activate_subject/<int:pk>', activate_subject, name='activate_subject'),

    path('delete_subject/<int:pk>/', Delete_Subject.as_view(), name='delete_subject'),
    path('delete_subject_topic/<int:pk>/', Delete_Subject_Topic.as_view(), name='delete_subject_topic'),
    path('delete_topic_set/<int:pk>/', Delete_Topic_Set.as_view(), name='delete_topic_set'),
    path('delete_set_element/<int:pk>/', Delete_Set_Element.as_view(), name='delete_set_element'),
    path('delete_set/<int:pk>/', Delete_Set.as_view(), name='delete_set'),
    path('delete_playlist/<int:pk>/', Delete_Playlist.as_view(), name='delete_playlist'),
    path('delete_playlist_set/<int:pk>/', Delete_Playlist_Set.as_view(), name='delete_playlist_set'),

    path('add_new_subject/<str:container>/<str:direction>/', Add_New_Subject.as_view(), name='add_new_subject'),
    path('add_new_topic_into_subject/<int:container>/<str:direction>/', Add_New_Topic_Into_Subject.as_view(), name='add_new_topic_into_subject'),
    path('add_new_set_into_topic/<int:container>/<str:direction>/', Add_New_Set_Into_Topic.as_view(), name='add_new_set_into_topic'),
    path('add_new_element_into_set/<int:container>/<str:direction>/', add_new_element_into_set, name='add_new_element_into_set'),
    path('add_new_playlist/<str:direction>/', Add_New_Playlist.as_view(), name='add_new_playlist'),

    path('insert_topic_into_subject/<int:pk>/', Insert_Topic_Into_Subject.as_view(), name='insert_topic_into_subject'),
    path('insert_set_into_topic/<int:pk>/', Insert_Set_Into_Topic.as_view(), name='insert_set_into_topic'),
    path('insert_element_into_set/<int:pk>/', Insert_Element_Into_Set.as_view(), name='insert_element_into_set'),
    path('insert_set_into_playlist/<int:pk>/', Insert_Set_Into_Playlist.as_view(), name='insert_set_into_playlist'),

    path('sets_types/', Show_Set_Types.as_view(), name='sets_types'),
    path('show_sets_for_set_types/<int:pk>/', Show_Sets_For_Set_Types.as_view(), name='show_sets_for_set_types'),

    path('delete_set_type/<int:pk>/', Delete_Set_Type.as_view(), name='delete_set_types'),
    path('add_new_set_type/', Add_New_Set_Type.as_view(), name='add_new_set_type'),
    
    path('update_set_type/<int:pk>/', Update_Set_Type.as_view(), name='update_set_type'),
    path('add_new_part_type_into_set_type/<int:container>/', Add_New_Part_Type_Into_Set_Type.as_view(), name='add_new_part_type_into_set_type'),
    path('change_part_type_position/<int:container>/<int:position>/<str:direction>/', Change_Part_Type_Position.as_view(), name='change_part_type_position'),
    path('delete_path_type_out_of_set_type/<int:pk>/', Delete_Part_Type_Out_Of_Set_Type.as_view(), name='delete_path_type_out_of_set_type'),

    path('parts_types/', Show_Parts_Types.as_view(), name='parts_types'),
    path('update_part_type/<int:pk>/', Update_Part_Type.as_view(), name='update_part_type'),
    path('add_new_part_type/', Add_New_Part_Type.as_view(), name='add_new_part_type'),
    path('delete_part_type/<int:pk>/', Delete_Part_Type.as_view(), name='delete_part_type'),

    path('languages/', Show_Languages.as_view(), name='languages'),
    path('update_language/<int:pk>/', Update_Language.as_view(), name='update_language'),
    path('add_new_language/', Add_New_Language.as_view(), name='add_new_language'),
    path('delete_language/<int:pk>/', Delete_Language.as_view(), name='delete_language'),

    path('save_comment', save_comment, name='save_comment'),
    path('save_item_color', save_item_color, name='save_item_color'),
    path('save_part_type_color', save_part_type_color, name='save_part_type_color'),
    path('change_set_notes_availability/<int:id>/', change_set_notes_availability, name='change_set_notes_availability'),
    path('notes/', notes, name='notes'),

    path('import_common_formated_set/', import_common_formated_set, name='import_common_formated_set'),
    path('import_native_formated_set/', import_native_formated_set, name='import_native_formated_set'),

    path('export_native_formated_set', export_native_formated_set, name='export_native_formated_set'),
    path('export_common_formated_set/<int:set>/', export_common_formated_set, name='export_common_formated_set'),

    path('user_profile/', User_Profile.as_view(), name='user_profile'),
    path('assign_timezone/', assign_timezone, name='assign_timezone'),

    path('', include('pronunciation.urls')),
    path(r'clean_parts/', clean_parts),
    path(r'', Show_Subjects_List.as_view(), name='start_page')
]