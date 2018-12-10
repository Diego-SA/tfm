from git import Repo
import os

# GitHubProject to analyze
project = 'https://github.com/iluwatar/java-design-patterns'
project_name = project.split('/')[-1]
# Commit SHA
sha = '1d12d94bac64564a70faec05af21d33e17465b7d'
# SourceMeter directory
sourceMeter_link = 'C:\\Users\\Diego\\Downloads\\SourceMeter-8.2.0-x64-windows\\Java\\SourceMeterJava.exe'

dir_clone = 'repo'
results = 'Results'

# Download project
repo = Repo.clone_from(project, dir_clone)

commit = None
# Get commit object
for c in repo.iter_commits():
    if (c.hexsha == sha):
        commit = c
        break

if (commit is None):
    print("Commit not found")
else:
    # Deny all files, then will only allow touched files
    filter_txt = open("filter.txt", "w")
    filter_txt.write("-[^\.]*.java\n")
    
    # Select .java touched files and put in filter.txt
    for file in commit.stats.files.keys():
        if len(file) > 5 and file[-5:] == '.java':
            filter_txt.write('+' + file.split('/')[-1] + '\n')
    filter_txt.close()
    
    #Get SourceMeter metrics of the touched files
    args = sourceMeter_link + " -projectName="+project_name+" -projectBaseDir="+dir_clone+" -resultsDir="+results+" -externalHardFilter=filter.txt" 
    exe = os.system(args)
    
    if (exe != 0):
        print('Something went wrong in SourceMeter execution')