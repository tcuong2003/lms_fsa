from django.shortcuts import render, get_object_or_404, redirect
from .models import Subject, Material
from .forms import SubjectForm, MaterialUploadForm
from module_group.models import ModuleGroup
from django.http import HttpResponse, FileResponse
from django.contrib import messages
import zipfile
import os
import mimetypes
from main.forms import ExcelImportForm
from .forms import SubjectForm
from main.forms import ExcelImportForm
import openpyxl
import pandas as pd

# Subject list view
def subject_list(request):
    module_groups = ModuleGroup.objects.all()
    subjects = Subject.objects.all()

    form = ExcelImportForm()


    return render(request, 'subject_list.html', {
        'module_groups': module_groups,
        'subjects': subjects,
        'form': form
    })

# Add a new subject
def subject_add(request):
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Subject added successfully.')
            return redirect('subject:subject_list')
        else:
            messages.error(request, 'Failed to add subject. Please check the form for errors.')
    else:
        form = SubjectForm()
    
    return render(request, 'subject_form.html', {'form': form})

# Edit a subject
def subject_edit(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    if request.method == 'POST':
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            form.save()
            messages.success(request, 'Subject updated successfully.')
            return redirect('subject:subject_list')
        else:
            messages.error(request, 'Failed to update subject. Please check the form for errors.')
    else:
        form = SubjectForm(instance=subject)
    
    return render(request, 'subject_form.html', {'form': form})

# Delete a subject
def subject_delete(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    if request.method == 'POST':
        subject.delete()
        messages.success(request, 'Subject deleted successfully.')
        return redirect('subject:subject_list')
    
    return render(request, 'subject_confirm_delete.html', {'subject': subject})

# Delete material
def delete_material(request, pk):
    material = get_object_or_404(Material, pk=pk)
    subject = material.subject  # Assuming material has a ForeignKey to subject
    if request.method == 'POST':
        material.delete()
        messages.success(request, 'Material deleted successfully.')
    return redirect('subject:subject_materials', subject_id=subject.pk)

def upload_material(request):
    if request.method == 'POST':
        subject_id = request.POST.get('subject_id')
        subject = get_object_or_404(Subject, pk=subject_id)
        material_type = request.POST['material_type']
        
        # Get the files and Google Drive link
        files = request.FILES.getlist('file')
        google_drive_link = request.POST.get('google_drive_link')

        if files:
            # If files are provided, save them
            for file in files:
                material = Material(file=file, subject=subject, material_type=material_type)
                material.save()
        elif google_drive_link:
            # If a Google Drive link is provided, save it
            material = Material(google_drive_link=google_drive_link, subject=subject, material_type=material_type)
            material.save()
        else:
            # If neither file nor Google Drive link is provided, show an error
            messages.error(request, 'Please upload a file or provide a Google Drive link.')
            return redirect('subject:subject_materials', subject_id=subject.pk)

        messages.success(request, 'Materials uploaded successfully.')
        return redirect('subject:subject_materials', subject_id=subject.pk)

    subjects = Subject.objects.all()
    form = MaterialUploadForm()  # Create an instance of the form
    return render(request, 'materials/upload_materials.html', {
        'subjects': subjects,
        'form': form,  # Pass the form to the template
    })


def upload_material3(request):
    if request.method == 'POST':
        subject_id = request.POST.get('subject_id')
        subject = get_object_or_404(Subject, pk=subject_id)
        material_type = request.POST['material_type']
        google_drive_link = request.POST.get('google_drive_link')

        files = request.FILES.getlist('file')

        # Check if files were uploaded or a Google Drive link was provided
        if files:
            for file in files:
                material = Material(file=file, subject=subject, material_type=material_type)
                material.save()
        elif google_drive_link:
            material = Material(google_drive_link=google_drive_link, subject=subject, material_type=material_type)
            material.save()

        messages.success(request, 'Materials uploaded successfully.')
        return redirect('subject:subject_materials', subject_id=subject.pk)

    subjects = Subject.objects.all()
    form = MaterialUploadForm()  # Create an instance of the form
    return render(request, 'materials/upload_materials.html', {
        'subjects': subjects,
        'form': form,  # Pass the form to the template
    })


def upload_material2(request):
    if request.method == 'POST':
        subject_id = request.POST.get('subject_id')
        subject = get_object_or_404(Subject, pk=subject_id)
        material_type = request.POST['material_type']
        
        files = request.FILES.getlist('file')
        
        for file in files:
            material = Material(file=file, subject=subject, material_type=material_type)
            material.save()

        messages.success(request, 'Materials uploaded successfully.')
        return redirect('subject:subject_materials', subject_id=subject.pk)

    subjects = Subject.objects.all()
    form = MaterialUploadForm()  # Create an instance of the form
    return render(request, 'materials/upload_materials.html', {
        'subjects': subjects,
        'form': form,  # Pass the form to the template
    })


# Display materials by subject view
def subject_materials(request, subject_id):
    subject = get_object_or_404(Subject, pk=subject_id)
    
    materials = Material.objects.filter(subject=subject)

    # Retrieve the materials
    assignments = subject.materials.filter(material_type='assignments')
    labs = subject.materials.filter(material_type='labs')
    lectures = subject.materials.filter(material_type='lectures')
    references = subject.materials.filter(material_type='references')
    
    # Sort materials by file name using Python
    assignments = sorted(assignments, key=lambda m: m.file.name if m.file else '')
    labs = sorted(labs, key=lambda m: m.file.name if m.file else '')
    lectures = sorted(lectures, key=lambda m: m.file.name if m.file else '')
    references = sorted(references, key=lambda m: m.file.name if m.file else '')

    return render(request, 'materials/subject_materials.html', {
        'subject': subject,
        'materials': materials,
        'assignments': assignments,
        'labs': labs,
        'lectures': lectures,
        'references': references,
    })


def download_all_materials(request, material_type):
    zip_filename = f'{material_type}s.zip'
    
    # Create a zip file
    with zipfile.ZipFile(zip_filename, 'w') as zip_file:
        materials = Material.objects.filter(material_type=material_type)  # Use 'material_type' instead of 'type'
        for material in materials:
            zip_file.write(material.file.path, arcname=os.path.basename(material.file.name))

    # Serve the zip file
    response = HttpResponse(open(zip_filename, 'rb'), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename={zip_filename}'
    
    # Optionally, delete the zip file after sending it
    # os.remove(zip_filename)
    
    return response


# Export Subjects to Excel
def export_subjects(request):
    # Create a workbook and add a worksheet
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=lms_subject.xlsx'
    
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.title = 'Subjects'
    
    # Define the columns
    columns = ['code', 'name', 'description']
    worksheet.append(columns)
    
    # Fetch all Subjects and write to the Excel file
    for subject in Subject.objects.all():
        worksheet.append([subject.code, subject.name, subject.description])
    
    workbook.save(response)
    return response

def import_subjects(request):
    if request.method == 'POST':
        form = ExcelImportForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['excel_file']
            try:
                # Read the Excel file
                df = pd.read_excel(uploaded_file)
                subjects_imported = 0  # Counter for Subjects successfully imported

                # Loop over the rows in the DataFrame
                for index, row in df.iterrows():
                    name = row.get("name")
                    code = str(row.get("code"))
                    description = row.get("description")

                    print(f"Processing row: {name}, {code}, {description}")  # Debugging

                   
                    # Check if the Subject already exists
                    if not Subject.objects.filter(name=name).exists():
                        # Create and save the new Subject
                        Subject.objects.create(
                            name=name,
                            code=code,
                            description=description
                        )
                        subjects_imported += 1
                        print(f"Subject {name} created")  # Debugging
                    else:
                        messages.warning(request, f"Subject '{name}' already exists. Skipping.")
                        print(f"Subject {name} already exists")  # Debugging

                # Feedback message
                if subjects_imported > 0:
                    messages.success(request, f"{subjects_imported} Subjects imported successfully!")
                else:
                    messages.warning(request, "No Subjects were imported.")

            except Exception as e:
                messages.error(request, f"An error occurred during import: {e}")
                print(f"Error during import: {e}")  # Debugging

            return redirect('subject:subject_list')
    else:
        form = ExcelImportForm()

    return render(request, 'Subject_list.html', {'form': form})


def view_material11(request, material_id):
    material = get_object_or_404(Material, id=material_id)
    # Assuming you're returning the file or rendering a page with the file
    response = HttpResponse(material.file, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{material.file.name}"'
    return response

def view_material(request, material_id):
    # Get the material object
    material = get_object_or_404(Material, id=material_id)

    # Get the file path
    file_path = material.file.path
    file_type = material.file.name.split('.')[-1].lower()

    # Define supported types for preview
    supported_types = ['pdf', 'txt', 'xls', 'doc', 'docx']

    if file_type in supported_types:
        # If the file is supported, open it as a FileResponse
        file = open(file_path, 'rb')
        mime_type, _ = mimetypes.guess_type(file_path)
        return FileResponse(file, content_type=mime_type)
    else:
        # If not supported, return an error or download the file instead
        return HttpResponse("Viewing this file type is not supported.", status=400)

