# views.py
from django.shortcuts import render, redirect
from django.http import HttpResponse
import pandas as pd
import zipfile
from io import BytesIO, StringIO
from .forms import ExamGenerationForm, ExcelUploadForm, MultipleTxtUploadForm
from module_group.models import ModuleGroup
from tools.library.utils import generator, excel_to_json
from tools.library.txtToJson import txt_to_json, extract_code_name
from django.core.files.base import ContentFile
import os
from django.conf import settings
from django.urls import reverse
from datetime import datetime
from django.core.files.storage import default_storage


def export_txt_to_json(request):
    module_groups = ModuleGroup.objects.all()
    file_names = []

    if request.method == 'POST':
        num_files = int(request.POST.get('number_of_files', 1))
        form = MultipleTxtUploadForm(request.POST, num_files=num_files)

        if form.is_valid():
            # Create a ZIP file in memory
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for i in range(num_files):
                    txt_content = form.cleaned_data.get(f'txt_file_{i}')
                    if txt_content:
                        file_name = extract_code_name(txt_content)
                        if not file_name:
                            file_name = f'file_{i + 1}'
                        file_like = StringIO(txt_content)
                        json_output = txt_to_json(file_like, file_name)  # Convert TXT content to JSON
                        json_file_name = f'{file_name}.json'

                        # Save JSON data to a file in the ZIP archive
                        zip_file.writestr(json_file_name, json_output)
                        file_names.append(json_file_name)

            zip_buffer.seek(0)

            # Generate a unique filename for the ZIP file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            zip_filename = f'json_files_{timestamp}.zip'
            zip_file_path = os.path.join(settings.MEDIA_ROOT, zip_filename)

            # Save the ZIP file to a temporary location
            with open(zip_file_path, 'wb') as f:
                f.write(zip_buffer.getvalue())

            # Generate the download URL with the filename
            download_url = reverse('tools:download_zip_file', args=[zip_filename])
            success_message = 'Your JSON files have been successfully created. Click the button below to download.'

            return render(request, 'export_txt_to_json.html', {
                'module_groups': module_groups,
                'file_names': file_names,
                'success_message': success_message,
                'download_url': download_url,
            })

    else:
        form = MultipleTxtUploadForm(initial={'number_of_files': 1})  # Default to 1 file

    return render(request, 'export_txt_to_json.html', {
        'module_groups': module_groups,
        'form': form
    })


def download_zip_file(request):
    zip_file_path = os.path.join(settings.MEDIA_ROOT, 'exported_data.zip')
    if os.path.exists(zip_file_path):
        with open(zip_file_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/zip')
            response['Content-Disposition'] = 'attachment; filename="exported_data.zip"'
            return response
    else:
        return HttpResponse("File not found.", status=404)


def export_excel_to_json(request):
    module_groups = ModuleGroup.objects.all()
    form = ExcelUploadForm()
    json_data = None
    json_file_name = None

    if request.method == 'POST':
        form = ExcelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['excel_file']
            # Convert the uploaded Excel file to JSON
            df_combined = pd.read_excel(excel_file)
            json_data = excel_to_json(df_combined)
            json_file_name = 'exported_data.json'

            # Show the JSON data and provide a download link
            return render(request, 'export_excel_to_json.html', {
                'module_groups': module_groups,
                'form': form,
                'json_data': json_data,
                'json_file_name': json_file_name
            })

    return render(request, 'export_excel_to_json.html', {
        'module_groups': module_groups,
        'form': form
    })

def download_json_file(request):
    json_file_name = request.GET.get('file_name', 'data.json')
    json_output = request.GET.get('json_data', '{}')

    response = HttpResponse(json_output, content_type='application/json')
    response['Content-Disposition'] = f'attachment; filename="{json_file_name}"'
    return response


def exam_generator_view(request):
    module_groups = ModuleGroup.objects.all()
    form = ExamGenerationForm()
    success_message = None
    download_url = None

    if request.method == 'POST':
        form = ExamGenerationForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['excel_file']
            number_of_exams = form.cleaned_data['number_of_exams']
            number_of_questions_per_exam = form.cleaned_data['number_of_questions']

            # Create a BytesIO object to hold the ZIP file data
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                excel_data = pd.ExcelFile(excel_file)
                sheet_names = excel_data.sheet_names
                total_files_created = 0

                for count in range(number_of_exams):
                    output_file, df_combined = generator(excel_file, {sheet: number_of_questions_per_exam for sheet in sheet_names})
                    json_output = excel_to_json(df_combined)

                    # Save JSON data to a file in the ZIP archive
                    json_file_name = f'exam_{count + 1}.json'
                    zip_file.writestr(json_file_name, json_output)
                    total_files_created += 1

                    # Save the Excel file to the ZIP archive
                    excel_file_name = f'exam_{count + 1}.xlsx'
                    zip_file.writestr(excel_file_name, output_file.getvalue())
                    total_files_created += 1

            zip_buffer.seek(0)

            # Generate a unique filename with a timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            zip_filename = f'exams_{timestamp}.zip'

            # Save the ZIP file to the media directory
            zip_file_path = os.path.join(settings.MEDIA_ROOT, zip_filename)
            with open(zip_file_path, 'wb') as f:
                f.write(zip_buffer.getvalue())

            # Provide the list of files created and the ZIP download URL
            download_url = reverse('tools:download_zip_file', args=[zip_filename])
            success_message = f'{total_files_created} files were successfully created. Click the button below to download.'

            return render(request, 'generate_exams.html', {
                'module_groups': module_groups,
                'form': form,
                'success_message': success_message,
                'download_url': download_url,
            })

    return render(request, 'generate_exams.html', {
        'module_groups': module_groups,
        'form': form
    })


import os
from django.conf import settings
from django.http import HttpResponse, Http404

def download_zip_file(request, filename):
    file_path = os.path.join(settings.MEDIA_ROOT, filename)
    if not os.path.exists(file_path):
        raise Http404("File does not exist")
    
    with open(file_path, 'rb') as f:
        response = HttpResponse(f.read(), content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
