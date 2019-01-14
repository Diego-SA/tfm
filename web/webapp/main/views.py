from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods

from .forms import BuildForm

import random

# Create your views here.
def index(request):
	# GET method -> Write form
	if request.method == 'GET':
		form = BuildForm()
	# POST method -> If there's data, process it and call function
	elif request.method == 'POST':
		form = BuildForm(request.POST)
		if form.is_valid():
			project_url = form.cleaned_data['project_url']
			commit_sha = form.cleaned_data['commit_sha']
			
			# Temporary: random number to create cloned project
			random_n = random.randint(1,10000000)
			html = '<p>URL: ' + project_url + '. Commit: ' + commit_sha + '</p>'
			# Analyze project and predict bugs
			generateRepoAtts(project_url, commit_sha, random_n)
			html = html + predictBuggyFiles(project_url)
			
			return HttpResponse(html)
    
	return render(request, 'build_template.html', {'form':form})
	
	
from git import Repo
import subprocess
import os
import shutil
import stat
import re

def generateRepoAtts(project_url, commit_sha, random_n):
	project_name = project_url.split('/')[-1]

	windows = os.environ['WINDOWS']
	print('Valor de windows: ' + windows)
	
	# SourceMeter directory (for local developement)
	if (windows):
		sourceMeter_link = 'static/SourceMeter-8.2.0-x64-windows/Java/SourceMeterJava.exe'
	else:
		sourceMeter_link = 'static/SourceMeter-8.2.0-x64-linux/Java/SourceMeterJava'
	
	# Directory where we will save project clone and metrics analysis
	dir_clone = project_name + '_repo' + str(random_n)
	results = 'Results'

	# Download project
	repo = Repo.clone_from(project_url, dir_clone)

	# Get commit object
	commit = None
	for c in repo.iter_commits():
		if (c.hexsha == commit_sha):
			commit = c
			break
	if (commit is None):
		print("Commit not found")
	else:
		# Deny all files, then will only allow touched files
		filter_txt = open("filter.txt", "w")
		filter_txt.write("-[^\.]*.java\n")
		
		files = []
		# Select .java touched files and put in filter.txt
		for file in commit.stats.files.keys():
			if len(file) > 5 and file[-5:] == '.java' and file not in files and '{' not in file:
				files.append(file)
				filter_txt.write('+' + file.replace('/', '\\\\') + '\n')
		filter_txt.close()
		
		#Add execution permission to SourceMeter
		st = os.stat(sourceMeter_link)
		os.chmod(sourceMeter_link, st.st_mode | stat.S_IEXEC)
		
		print(os.environ['JAVA_HOME'])
		print(os.environ['PATH'])
		#Get SourceMeter metrics of the touched files
		args = sourceMeter_link + " -projectName="+project_name+" -projectBaseDir="+dir_clone+" -resultsDir="+results+" -externalHardFilter=filter.txt" 
		args = args.split()
		exe = subprocess.run(args)
		
		if (exe != 0):
			print('Something went wrong in SourceMeter execution')
		else:
			print('No problems executing SourceMeter')
	
import pandas as pd
import os
import pickle

def predictBuggyFiles(project_url):

	project_name = project_url.split('/')[-1]
	data_dir = 'Results/' + project_name + '/java'
	last_analysis = sorted(os.listdir(data_dir), reverse = True)[0]

	# Look for -Class.csv file
	class_df = None
	for file in os.listdir(data_dir + '/' + last_analysis):
		if (len(file) > 10 and file[-10:] == '-Class.csv'):
			class_df = pd.read_csv(data_dir + "/" + last_analysis + "/" + file, sep = ',')
			break

	# Delete non-numeric attributes, and attributes wich doesn't appear in train data
	class_df = class_df.set_index("ID")

	prediction_df = class_df.drop(['Name', 'LongName', 'Parent', 'Component', 'Path', 'Runtime Rules'], axis = 1)
	classifier_dir = 'static\\RandomForestv1.sav'
	# Load classifier and predict
	clf = pickle.load(open(classifier_dir, 'rb'))

	prediction = clf.predict(prediction_df)

	html = ""
	for idx, predict in zip(prediction_df.index, prediction):
		if (predict):
			html = html + "<p>Class " + class_df.loc[idx, 'Name'] + " probably has bugs</p>"
		else:
			html = html + "<p>Class " + class_df.loc[idx, 'Name'] + " probably hasn't bugs</p>"		
	
	return html

# Borrar los archivos de una carpeta
# De momento lanza un error de tipo PermissionError. Acceso denegado
def deleteFiles(path):
    os.chmod(path, stat.S_IWRITE)
    
    for file_ in os.listdir(path):
        filePath=os.path.join(path, file_)
        if os.path.isdir(filePath):
            deleteFiles(filePath)
        else:
            os.chmod(filePath, stat.S_IWRITE)
            os.remove(filePath)