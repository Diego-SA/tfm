from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import redirect

from .forms import BuildForm
from git import Repo
from rq import Queue
import subprocess
import shutil
import stat
import time
import redis
import pandas as pd
import os
import pickle
import logging

windows = False

if os.name == 'nt':  # Windows local
	windows = True
	worker_conn = redis.from_url(os.getenv('REDISTOGO_URL', 'redis://localhost:6379/'))
elif os.getenv('LOCAL') == 'true':  # linux (local docker compose)
	worker_conn = redis.from_url('redis://redis:6379/')
else:  # heroku
	worker_conn = redis.from_url(os.environ.get("REDIS_URL"))

q = Queue(connection=worker_conn)


# Create your views here.
def index(request):
	# GET method -> Write form
	if request.method == 'GET':
		form = BuildForm()
		return render(request, 'build_template.html', {'form': form})
	# POST method -> If there's data, process it and call function
	elif request.method == 'POST':

		form = BuildForm(request.POST)
		if form.is_valid():
			project_url = form.cleaned_data['project_url']
			commit_sha = form.cleaned_data['commit_sha']

			job1 = q.enqueue(generate_repo_atts, project_url, commit_sha)
			time.sleep(1)  # dar tiempo para que job1 acabe rápidamente si ve que ya están los datos
			# no se pueden usar watchdogs porque esto es front end, y el worker se baja las carpetas
			# en su espacio no compartido (heroku no deja compartir volúmenes entre contenedores)
			if not job1.status == 'finished':
				return HttpResponse("Descargando datos.<p> Por favor vuelve más tarde e introduce los mismos valores.")
			job2 = q.enqueue(predict_buggy_files, project_url, commit_sha)
			while not job2.status == 'finished':  # es rápido
				time.sleep(2)
			return HttpResponse(job2.result)

def results(request):
    return HttpResponse("Viendo resultados")

# noinspection PyPep8,PyPep8
def generate_repo_atts(project_url, commit_sha):

	# si no existe, se realiza.
	project_name = project_url.split('/')[-1]
	results_dir = 'Results/' + project_name + '/java'

	if not os.path.exists(results_dir):

		if windows:
			source_meter_link = '../static/SourceMeter-8.2.0-x64-windows/Java/SourceMeterJava.exe'
		else:
			source_meter_link = '../static/sourcemeter-8.2.0-x64-linux/Java/SourceMeterJava'

		# Directory where we will save project clone and metrics analysis
		dir_clone = project_name + '_' + commit_sha
		results = 'Results'

		# Download project

		try:
			repo = Repo.clone_from(project_url, dir_clone)
		except Exception as e:
			logging.exception(e)
			logging.error('wrong repository url or it was previously downloaded and not removed yet')
			return -1

		# Get commit object
		commit = None
		for c in repo.iter_commits():
			if c.hexsha == commit_sha:
				commit = c
				break
		if commit is None:
			print("Commit not found")
			return -1
		else:
			# Deny all files, then will only allow touched files
			filter_txt = open("filter.txt", "w")
			filter_txt.write("-[^\.]*.java\n")

			files = []
			# Select .java touched files and put in filter.txt
			for file in commit.stats.files.keys():
				if len(file) > 5 and file[-5:] == '.java' and file not in files and '{' not in file:
					files.append(file)
					if windows:
						filter_txt.write('+' + file.replace('/', '\\\\') + '\n')
					else:
						filter_txt.write('+' + file + '\n')
			filter_txt.close()

			# Add execution permission to SourceMeter
			st = os.stat(source_meter_link)
			os.chmod(source_meter_link, st.st_mode | stat.S_IEXEC)

			# Get SourceMeter metrics of the touched files
			args = source_meter_link + " -projectName=" + project_name + " -projectBaseDir=" + dir_clone +\
				" -resultsDir=" + results + " -externalHardFilter=filter.txt -JVMOptions=-Xmx128m -maximumThreads=8"

			args = args.split()
			exe = subprocess.run(args)
			if exe.returncode != 0:
				print('Something went wrong in SourceMeter execution')
			else:
				print('Ejecución correcta')



def predict_buggy_files(project_url, commit_sha):
	project_name = project_url.split('/')[-1]
	data_dir = 'Results/' + project_name + '/java'

	last_analysis = sorted(os.listdir(data_dir), reverse=True)[0]

	# Look for -Class.csv file
	class_df = None
	for file in os.listdir(data_dir + '/' + last_analysis):
		if len(file) > 10 and file[-10:] == '-Class.csv':
			class_df = pd.read_csv(data_dir + "/" + last_analysis + "/" + file, sep=',')
			break

	# Delete non-numeric attributes, and attributes wich doesn't appear in train data
	class_df = class_df.set_index("ID")

	prediction_df = class_df.drop(['Name', 'LongName', 'Parent', 'Component', 'Path', 'Runtime Rules'], axis=1)
	if os.name == 'nt':  # windows
		classifier_dir = 'models\\RandomForestv1.sav'
	else:
		classifier_dir = 'models/RandomForestv1.sav'
	# Load classifier and predict
	clf = pickle.load(open(classifier_dir, 'rb'))

	prediction = clf.predict(prediction_df)

	html = ""
	for idx, predict in zip(prediction_df.index, prediction):
		if predict:
			html = html + "<p>Class " + class_df.loc[idx, 'Name'] + " probably has bugs</p>"
		else:
			html = html + "<p>Class " + class_df.loc[idx, 'Name'] + " probably hasn't bugs</p>"

	# Clean non-necessary files
	clean_files(project_url.split('/')[-1] + '_' + commit_sha)

	return html


def clean_files(dir_project):
	# Eliminar repositorio con os.system. GitPython no deja
	# una cache que no permite borrarla con shutil.rmtree en windows.
	if windows:
		os.system('rmdir /S /Q "{}"'.format(dir_project))
	else:
		shutil.rmtree(dir_project, ignore_errors=True)

	# Borrar resultados
	shutil.rmtree('Results', ignore_errors=True)
	# Eliminar archivo filter.txt
	os.remove('filter.txt')
