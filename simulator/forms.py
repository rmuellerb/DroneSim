from django import forms
from .models import SimulatorSettings

class ModeChooseForm(forms.Form):
    CHOICES = [('static', 'Static'), ('live', 'Live')]

    def __init__(self, *args, **kwargs):
        super(ModeChooseForm, self).__init__(*args, **kwargs)
        current_settings = SimulatorSettings.objects.first()
        current_mode = current_settings.mode if current_settings else 'static'  # default value
        self.fields['simulator_mode'] = forms.ChoiceField(choices=self.CHOICES, widget=forms.RadioSelect, initial=current_mode)
