from django.shortcuts import render
from django.http import HttpResponse

from .forms import BuildForm
from git import Repo
import git
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
import zipfile
import json
import boto3

windows = False

if os.name == 'nt':  # Windows
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
		form = BuildForm(request.POST, request.FILES)
		if form.is_valid():
			# Obtener el archivo
			file = request.FILES['file']
			
			# Bucket de Amazon S3
			S3_BUCKET = 'tfm'
			print("S3_BUCKET: ", S3_BUCKET)
			
			print("Archivo a subir: ", file.name)
			
			s3 = boto3.client('s3',
			aws_access_key_id='AKIAJ4HH3WCBQA2Q4ANA',
			aws_secret_access_key='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')

			s3.upload_file(file.temporary_file_path(), S3_BUCKET, file.name)
			
			print("Archivo subido a S3")
			
			# Extraer el archivo en el volumen compartido
			#archive = zipfile.ZipFile(file.temporary_file_path(), 'r')
			#archive.extractall('/data')
			#archive.close()

			# Mandar trabajo a la cola
			job1 = q.enqueue(generate_repo_atts, file.name[:-4])
			time.sleep(1)  # dar tiempo para que job1 acabe rápidamente si ve que ya están los datos
			# no se pueden usar watchdogs porque esto es front end, y el worker se baja las carpetas

			# en su espacio no compartido (heroku no deja compartir volúmenes entre contenedores)
			if not job1.status == 'finished':
				html = """
					<html><head><style>	
						@import url(https://fonts.googleapis.com/css?family=Roboto:400,300,600,400italic);
						* {
						  margin: 0;
						  box-sizing: border-box;
						  -webkit-box-sizing: border-box;
						  -moz-box-sizing: border-box;
						  -webkit-font-smoothing: antialiased;
						  -moz-font-smoothing: antialiased;
						  -o-font-smoothing: antialiased;
						  font-smoothing: antialiased;
						  text-rendering: optimizeLegibility;
						}
						body {
						  font-family: "Roboto", Helvetica, Arial, sans-serif;
						  font-weight: 100;
						  font-size: 16px;
						  line-height: 30px;
						  color: #777;
						  background: #4CAF50;
						}
						
						#container {
						  width: 400px;
						  margin: 0 auto;
						  position: relative;
						}
						
						#contact {
						  background: #F9F9F9;
						  padding: 25px;
						  margin: 150px 0;
						  box-shadow: 0 0 20px 0 rgba(0, 0, 0, 0.2), 0 5px 5px 0 rgba(0, 0, 0, 0.24);
						}
						</style>
						<link rel="stylesheet" href="https://use.fontawesome.com/releases/v5.8.1/css/all.css" integrity="sha384-50oBUHEmvpQ+1lW4y57PTFmhCaXp0ML5d60M1M7uH2+nqUivzIebhndOJK28anvf" crossorigin="anonymous">
						</head>
						<body>
						<div id="container">
							<div id="contact">
								<h3> Descargando datos </h3>
								<h4> Por favor vuelve más tarde e introduce los mismos valores. </h4>
								<div style="font-size: 100px; display: grid; padding-top: 30px; padding-bottom: 20px">
								<i style="margin-left: auto; margin-right: auto;" class="fas fa-sync fa-spin"></i>
								</div>
							</div>
						</div>
						</body>
						</html>
				"""
				return HttpResponse(html)
			job2 = q.enqueue(predict_buggy_files, file.name[:-4])
			while not job2.status == 'finished':  # es rápido
				time.sleep(2)
			return HttpResponse(job2.result)


# noinspection PyPep8,PyPep8
def generate_repo_atts(file_name):
	# si no existe, se realiza.
	project_name = file_name
	results_dir = 'Results/' + project_name + '/java'
	file_zip = file_name + '.zip'
	if not os.path.exists(results_dir):

		if windows:
			source_meter_link = '../static/SourceMeter-8.2.0-x64-windows/Java/SourceMeterJava.exe'
		else:
			source_meter_link = '../static/sourcemeter-8.2.0-x64-linux/Java/SourceMeterJava'

		# Bucket de Amazon S3
		S3_BUCKET = 'tfm'
		
		s3 = boto3.client('s3',
		aws_access_key_id='AKIAJ4HH3WCBQA2Q4ANA',
		aws_secret_access_key='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')

		s3.download_file(S3_BUCKET, file_zip, file_zip)
		
		archive = zipfile.ZipFile(file_zip, 'r')
		archive.extractall()
		archive.close()
		
		print("Archivos: ", os.listdir())

		# Directory where we will save project clone and metrics analysis
		dir_clone = file_name
		results = 'Results'

		git_object = git.Git(file_name)
		# Log con respecto a rama master (apareceran cambios locales)
		loginfo = git_object.log('origin/master..HEAD')
		commits = []
		for p in loginfo.splitlines():
			if (p[:6] == 'commit'):
				commits = commits + [p[7:]]
		
		# Objeto Repo para poder coger los commits
		repo = git.Repo(file_name)

		# Deny all files, then will only allow touched files
		filter_txt = open("filter.txt", "w")
		filter_txt.write("-[^\.]*.java\n")

		files = []
		for c in commits:
			commit = repo.commit(c)
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


def predict_buggy_files(file_name):
	project_name = file_name
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
	
	html = """<html><head><style>	
	@import url(https://fonts.googleapis.com/css?family=Roboto:400,300,600,400italic);
	* {
	  margin: 0;
	  box-sizing: border-box;
	  -webkit-box-sizing: border-box;
	  -moz-box-sizing: border-box;
	  -webkit-font-smoothing: antialiased;
	  -moz-font-smoothing: antialiased;
	  -o-font-smoothing: antialiased;
	  font-smoothing: antialiased;
	  text-rendering: optimizeLegibility;
	}
	body {
	  font-family: "Roboto", Helvetica, Arial, sans-serif;
	  font-weight: 100;
	  font-size: 16px;
	  line-height: 30px;
	  color: #777;
	  background: #4CAF50;
	}
	
	.container {
	  max-width: 1000px;
	  width: 100%;
	  margin: 0 auto;
	  position: relative;
	}
	
	#contact {
	  background: #F9F9F9;
	  padding: 25px;
	  margin: 150px 0;
	  box-shadow: 0 0 20px 0 rgba(0, 0, 0, 0.2), 0 5px 5px 0 rgba(0, 0, 0, 0.24);
	}
		#contact button[type="submit"] {
	  cursor: pointer;
	  width: 100%;
	  border: none;
	  background: #4CAF50;
	  color: #FFF;
	  margin: 0 0 5px;
	  padding: 10px;
	  font-size: 15px;
	}

	#contact button[type="submit"]:hover {
	  background: #43A047;
	  -webkit-transition: background 0.3s ease-in-out;
	  -moz-transition: background 0.3s ease-in-out;
	  transition: background-color 0.3s ease-in-out;
	}

	#contact button[type="submit"]:active {
	  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.5);
	}
	
	#contact button[type="submit"] {
	  font: 400 12px/16px "Roboto", Helvetica, Arial, sans-serif;
	}
	
	.container-table100 {
	  width: 950px;
	  margin-left: auto;
	  margin-right: auto;

	}
	
	.wrap-table100 {
	  border-radius: 10px;
	  overflow: hidden;
	}

	.table {
	  width: 100%;
	  display: table;
	  margin: 0;
	}

	tr {
	  background: #fff;
	  margin-left: auto;
	  margin-right: auto;
	}

	.row.header {
	  color: #ffffff;
	  background: #4CAF50;
	}
	.row .cell:before {
		font-size: 12px;
		color: #808080;
		line-height: 1.2;
		text-transform: uppercase;
		font-weight: unset !important;
		margin-bottom: 13px;
	}
	.table, .row {
	  width: 100% !important;
	}

	.row:hover {
	  background-color: #ececff;
	}
	
	.row {
		border-bottom: 1px solid #f2f2f2;
		margin: 0;
	}

	.row .cell {
		border: none;
		padding-right: 10px;
		padding-left: 10px;
		padding-top: 15px;
		padding-bottom: 15px;
	}


	li {
		margin-left: 15 px;
	}
	
	p {
		margin-left: auto;
		margin-right: auto;
		
	}
	</style></head>
	<body>
	<div id="container">
	<div id="contact" style="width: 1000px; margin-left: auto; margin-right: auto ;">
	"""
	
    # Analisis descriptivo
    # Seleccionar variables mas correlacionadas
	class_df_descriptive = class_df[["Name", "CBO", "NLE", "RFC", "Complexity Metric Rules", "WMC", "Documentation Metric Rules", "Coupling Metric Rules", "TNLA", "WarningInfo", "Size Metric Rules"]]
	headers_complete = ["CBO", "NLE", "RFC", "Complexity Metric Rules", "WMC", "Documentation Metric Rules", "Coupling Metric Rules", "TNLA", "WarningInfo", "Size Metric Rules"]
	headers = ["CBO", "NLE", "RFC", "CXMR", "WMC", "DMR", "CPMR", "TNLA", "WI", "SMR"]
	# Dibujar cabecera
	html = html + "<div class='container-table100'><table class='wrap-table100' style= 'margin-left: auto; margin-right: auto'><tr class='row header'><th class='cell'>Class</th>"
	for header in headers:
		html = html + "<th class='cell'>" + header + "</th>"
	html = html + "</tr>"
	# Dibujar filas
	for index, row in class_df_descriptive.iterrows():
		html = html + "<tr class='row'>"
		html = html + "<th class='cell'>" + str(row["Name"]) + "</th>"
		for header in headers_complete:
			html = html + "<th class='cell'>" + str(row[header]) + "</th>"
		html = html + "</tr>"
	html = html + "</table></div>"
	
	# Leyenda de los atributos
	html = html + '<br>'
	html = html + '<p style="font-size: 25px; padding-bottom: 5px">Información sobre las métricas: </p>'
	html = html + """<ul type = "square">
         <li><b>CBO</b>: <i>Coupling Between Object classes</i>, número de usos de otras clases. Un valor muy alto de este valor indica que es muy dependiente de otros módulos, y por tanto más difícil de testear y utilizar, además de muy sensible a cambios. Si tiene un valor alto quizás debería revisar sus cambios.</li>
         <li><b>NLE</b>: <i>Nesting Level Else-If</i>, grado de anidamiento máximo de cada clase (bloques de tipo if-else-if cuentan como 1 nivel)</li>
         <li><b>RFC</b>: <i>Response set For Class</i>: combinación de número de métodos locales y métodos llamados de otras clases.</li>
         <li><b>CXMR</b>: <i>Complexity Metric Rules</i>, violaciones en las buenas prácticas relativas a métricas de complejidad. Si es distinto de 0, quizás deba revisar sus cambios.</li>
		 <li><b>WMC</b>: <i>Weigthed Methods per Class</i>, número de caminos independientes de una clase. Se calcula como la suma de la complejidad coclomática de los métodos locales y bloques de inicialización.</li>
		 <li><b>DMR</b>: <i>Documentation Metric Rules</i>, violaciones de buenas prácticas relativas a la cantidad de comentarios y documentación.</li>
		 <li><b>CPMR</b>: <i>Coupling Metric Rules</i>, violaciones en las buenas prácticas relativas al acoplamiento de las clases. Si es distinto de 0, quizás deba revisar sus cambios.</li>
		 <li><b>TNLA</b>: <i>Total Number of Local Attributes</i>, número de atributos locales de cada clase.</li>
		 <li><b>WI</b>: <i>Warning Info</i>, advertencias de tipo <i>WarningInfo</i> en cada clase</li>
		 <li><b>SMR</b>: <i>Size Metric Rules</i>, violaciones en las buenas prácticas relativas al tamaño de las clases. Si es distinto de 0, quizás deba revisar sus cambios.</li>
      </ul>"""
	
	# FASE BETA: Mostrar predicciones
	html = html + '<br>'
	html = html + """<button type="submit" onclick="showPredictions()">Ver predicción de bugs (BETA)</button>
	<script>
	function showPredictions() {
	  document.getElementById("prediction").style.display = "grid";
	}
	</script>"""
	
    # Prediccion de bugs
	html = html + "<div id='prediction' style='display:none'>"
	for idx, predict in zip(prediction_df.index, prediction):
		if predict:
			html = html + "<p>Class " + class_df.loc[idx, 'Name'] + " probably has bugs</p>"
		else:
			html = html + "<p>Class " + class_df.loc[idx, 'Name'] + " probably hasn't bugs</p>"
	html = html + "</div>"
		
		
	html = html + "</div></div></body></html>"

	# Clean non-necessary files
	clean_files(file_name)

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
	
