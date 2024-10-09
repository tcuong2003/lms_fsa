from django import forms
from training_program.models import TrainingProgram


# Form for creating and editing training programs
class TrainingProgramForm(forms.ModelForm):
    class Meta:
        model = TrainingProgram
        fields = ['program_name', 'program_code', 'description']



