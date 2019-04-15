from django import forms

class BuildForm(forms.Form):
	project_url = forms.CharField(label='URL del proyecto GitHub', max_length=100)
	commit_sha = forms.CharField(label='Commit SHA', max_length=50)
	file = forms.FileField()