from django import forms

class BuildForm(forms.Form):
	file = forms.FileField(widget=forms.FileInput(attrs={'class' : 'delete'}))