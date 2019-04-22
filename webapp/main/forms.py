from django import forms

class BuildForm(forms.Form):
	file = forms.FileField()