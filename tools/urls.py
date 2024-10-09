from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'tools'  # Register the 'tools' namespace

urlpatterns = [
    path('exam-generator/', views.exam_generator_view, name='exam_generator_view'),
    path('export_excel_to_json/', views.export_excel_to_json, name='export_excel_to_json'),
    path('export_txt_to_json/', views.export_txt_to_json, name='export_txt_to_json'),
    path('download_json/', views.download_json_file, name='download_json_file'),
    path('download_zip_file/<str:filename>/', views.download_zip_file, name='download_zip_file'),  # Updated URL pattern
   
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)