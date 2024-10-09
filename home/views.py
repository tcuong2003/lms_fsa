import os
import pandas as pd
from django.shortcuts import render
from django.conf import settings

def get_home(request):
    # Directory containing all Excel files
    excel_dir = os.path.join(settings.BASE_DIR, 'media/data_csv')
    
    # List all .xls/.xlsx files in the directory
    excel_files = [f for f in os.listdir(excel_dir) if f.endswith('.xlsx') or f.endswith('.xls')]

    # If a file is selected, load its content
    selected_file = request.GET.get('selected_file')
    sub_courses_data = {}
    course_name = None
    split_sub_courses = []

    if selected_file:
        # Full file path
        file_path = os.path.join(excel_dir, selected_file)
        
        # Load the selected Excel file into a pandas DataFrame
        data = pd.read_excel(file_path)
        
        # Extract the course name and list of sub-courses
        course_name = data['course'].iloc[0]
        sub_course_list = data['sub_course'].dropna().unique()

        # Process the Excel content similar to how you did earlier
        for index, row in data.iterrows():
            sub_course = row['sub_course']
            module_name = row['module']
            sub_module_name = row['sub_module']

            if sub_course not in sub_courses_data:
                sub_courses_data[sub_course] = {}

            if module_name not in sub_courses_data[sub_course]:
                sub_courses_data[sub_course][module_name] = []

            if pd.notna(sub_module_name):
                content_html_list = row['content_html_list'] if pd.notna(row['content_html_list']) else ''
                img_list = row['img_list'] if pd.notna(row['img_list']) else ''
                video_url = row['video_url'] if pd.notna(row['video_url']) else ''

                content_html_list = content_html_list.replace('\\n', '<br>').replace("\\'", "'")

                sub_courses_data[sub_course][module_name].append({
                    'sub_module': sub_module_name,
                    'content_html_list': content_html_list,
                    'img_list': img_list,
                    'video_url': video_url
                })

        for sub_course in sub_course_list:
            if ':' in sub_course:
                title, description = sub_course.split(':', 1)
                split_sub_courses.append({
                    'title': title.strip(),
                    'description': description.strip(),
                    'modules': sub_courses_data[sub_course]
                })

    context = {
        'excel_files': excel_files,
        'selected_file': selected_file,
        'course_name': course_name,
        'split_sub_courses': split_sub_courses,
    }

    return render(request, 'course.html', context)
