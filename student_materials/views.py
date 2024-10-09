from subject.models import Material, Subject  # Ensure these are correct
from django.shortcuts import render, get_object_or_404
# from module_group.models import ModuleGroup
from django.http import HttpResponse, FileResponse, HttpResponseRedirect
import zipfile
import os
import mimetypes
from training_program.models import TrainingProgram
from training_program_subjects.models import TrainingProgramSubjects
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

# views.py
from django.http import JsonResponse
from django.db import models  # Import the models module

def get_subjects(request, training_program_id):
    # Fetch subjects related to the training program through the intermediary model
    training_program_subjects = TrainingProgramSubjects.objects.filter(program=training_program_id)
    subjects = Subject.objects.filter(trainingprogramsubjects__in=training_program_subjects).values('id', 'name')
    
    return JsonResponse(list(subjects), safe=False)

def get_material_types(request, subject_id):
    # Fetch materials related to the given subject and group by file type
    materials = Material.objects.filter(subject_id=subject_id).values('material_type').annotate(file_count=models.Count('id'))
    
    # Create a dictionary with material types and their corresponding counts
    material_types = {material['material_type']: material['file_count'] for material in materials}
    
    return JsonResponse(material_types)


# def get_material_types(request, subject_id):
#     materials = Material.objects.filter(subject_id=subject_id).values('file_type').annotate(file_count=models.Count('file_type'))
#     material_types = {material['file_type']: material['file_count'] for material in materials}
#     return JsonResponse(material_types)

def materials_view(request):
    subjects = Subject.objects.prefetch_related('materials').all()
    context = {
        'subjects': subjects,
    }
    return render(request, 'materials/subject_material.html', context)

def material_types(request, subject_id):
    subject = get_object_or_404(Subject, pk=subject_id)
    material_type = request.GET.get('material_type')

    # Filter materials based on the subject and material type
    materials = Material.objects.filter(subject=subject, material_type=material_type)
    
    # You can customize the response format as needed
    data = [{'id': material.id, 'name': material.file.name, 'type': material.get_material_type_display()} for material in materials]

    return JsonResponse({'materials': data}, status=200)


def display_materials_by_type(request, material_type):
    # Fetch materials by type (e.g., 'assignments', 'labs', etc.)
    materials = Material.objects.filter(material_type=material_type)
    material_data = []

    for material in materials:
        if material.file:  # If a file is uploaded
            file_type = material.get_file_type()  # Get the MIME type
            file_url = material.file.url
        elif material.google_drive_link:  # If a Google Drive link is provided
            file_type = 'Google Drive Link'  # Indicate this is a link
            file_url = material.google_drive_link
        else:
            file_type = 'No file'
            file_url = None  # No URL to provide

        material_data.append({
            'id': material.id,
            'name': material.file.name if material.file else 'N/A',
            'file_type': file_type,
            'size': material.file.size if material.file else None,
            'url': file_url,
        })

    return JsonResponse(material_data, safe=False)



def view_pdf(request, google_drive_link):
    # Check if the link is for a folder
    if "folders" in google_drive_link:
        # If it's a folder, construct the folder view link
        embed_link = google_drive_link  # Keep the original link for folders
        is_folder = True  # Flag to handle folder differently
    elif "file" in google_drive_link and "view" in google_drive_link:
        # If it's a file, extract the file ID and create the embed link
        file_id = google_drive_link.split("/d/")[1].split("/view")[0]
        embed_link = f"https://drive.google.com/file/d/{file_id}/preview"
        is_folder = False  # Flag for file
    else:
        # Fallback for unexpected URL formats
        embed_link = google_drive_link
        is_folder = False

    # Pass both the link and the flag to the template
    return render(request, 'materials/view_pdf.html', {'google_drive_link': embed_link, 'is_folder': is_folder})


# @login_required
def select_material(request):
    # Get the current user
    if request.user.is_authenticated:
        user = request.user
    else:
        # Default to a specific user, e.g., user with ID 4 (or handle anonymous users accordingly)
        user = User.objects.get(pk=4)  # Assuming user with ID 4 is the default or superadmin

    # Get the training programs assigned to the user
    user_training_programs = TrainingProgram.objects.all #user.training_programs.all()
    
    # Check if a training program has been selected
    training_program_id = request.GET.get('training_program_id')
    training_program = None  # Initialize to None by default

    if training_program_id:
        training_program = get_object_or_404(TrainingProgram, pk=training_program_id)
        # Filter through TrainingProgramSubjects to get the subjects for this training program
        training_program_subjects = TrainingProgramSubjects.objects.filter(program=training_program)
        subjects = Subject.objects.filter(trainingprogramsubjects__in=training_program_subjects)
    else:
        subjects = Subject.objects.all()  # Default to all subjects if no training program is selected

    # Handle subject and material selection logic
    fileSelect = request.GET.get("fileSelect", "assignments")  # Default to 'assignments'
    subject_id = request.GET.get('subject_id')

    # Default to the first subject if none is selected and subjects exist
    if not subject_id and subjects.exists():
        subject_id = subjects.first().id

    if subject_id:
        subject = get_object_or_404(Subject, pk=subject_id)
        materials = Material.objects.filter(subject=subject, material_type=fileSelect)

        # Filter materials by category
        assignments = subject.materials.filter(material_type='assignments')
        labs = subject.materials.filter(material_type='labs')
        lectures = subject.materials.filter(material_type='lectures')
        references = subject.materials.filter(material_type='references')

        # Sort materials by file name
        assignments = sorted(assignments, key=lambda m: m.file.name if m.file else '')
        labs = sorted(labs, key=lambda m: m.file.name if m.file else '')
        lectures = sorted(lectures, key=lambda m: m.file.name if m.file else '')
        references = sorted(references, key=lambda m: m.file.name if m.file else '')
    else:
        subject = None
        materials = None
        assignments = []
        labs = []
        lectures = []
        references = []

    return render(request, 'materials/subject_material.html', {
        'training_programs': user_training_programs,
        'selected_training_program': training_program,  # Pass the selected training program (if any)
        'subjects': subjects,
        'selected_subject': subject,
        'materials': materials,
        'assignments': assignments,
        'labs': labs,
        'lectures': lectures,
        'references': references,
        'fileSelect': fileSelect,  # Pass the selected category to the template
    })

from django.shortcuts import get_object_or_404
from django.http import FileResponse, HttpResponse
import mimetypes

def view_material(request, material_id):
    # Get the material object
    material = get_object_or_404(Material, id=material_id)

    # Check if there's a Google Drive link
    if material.google_drive_link:
        return HttpResponseRedirect(material.google_drive_link)

    # Check if the material has a local file
    if material.file:
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

    # If no valid file or Google Drive link, return an error message
    return HttpResponse("No valid file or Google Drive link associated with this material.", status=404)


# def view_material(request, material_id):
#     # Get the material object
#     material = get_object_or_404(Material, id=material_id)

#     # Get the file path
#     file_path = material.file.path
#     file_type = material.file.name.split('.')[-1].lower()

#     # Define supported types for preview
#     supported_types = ['pdf', 'txt', 'xls', 'doc', 'docx']

#     if file_type in supported_types:
#         # If the file is supported, open it as a FileResponse
#         file = open(file_path, 'rb')
#         mime_type, _ = mimetypes.guess_type(file_path)
#         return FileResponse(file, content_type=mime_type)
#     else:
#         # If not supported, return an error or download the file instead
#         return HttpResponse("Viewing this file type is not supported.", status=400)
    

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