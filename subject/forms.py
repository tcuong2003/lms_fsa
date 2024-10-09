from django import forms
from .models import Subject, Material

# Form for creating and editing subjects
class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'code', 'description']  # Added 'code' to the fields

# Form for uploading materials
class MaterialUploadForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = ['subject', 'material_type', 'file']

    material_type = forms.ChoiceField(choices=Material.MATERIAL_TYPE_CHOICES, widget=forms.RadioSelect)
    
    # Use a simple FileInput without multiple attribute
    file = forms.FileField()

