import os
import pandas as pd

# Dataframes with class and file attributes
classes = None
files = None

# Set the path of the input folder

data = os.getcwd()+os.sep+"datasets"+os.sep+"GitHubBugDataSet"+os.sep+"database"

data_output = os.getcwd()+os.sep+"datasets"+os.sep+"dataframes/"

# List out the projects inside input folder
projects = os.listdir(data)

# Look for Class and File files of each directory
for project in projects:
    
    # Look for each release
    releases = os.listdir(data + os.sep + project)
    for release in releases:
        
        # Look for each Class and File csv
        dataset = os.listdir(data + os.sep + project + os.sep + release)
        for file in dataset:
            
            # ....Class.csv file
            if file.endswith("Class.csv"):
                classdf = pd.read_csv(data + os.sep + project + os.sep + release + os.sep + file)
                
                if classes is None:
                    classes = classdf.copy()
                else:
                    classes = classes.append(classdf)
                    
            # File.csv file
            elif file.endswith("File.csv"):
                filedf = pd.read_csv(data + os.sep + project + os.sep + release + os.sep + file)

                if files is None:
                    files = filedf.copy()
                else:
                    files = files.append(filedf)
            
            # Other files. Ignore them
            else:
                continue
    # Delete duplicate rows
    classes = classes.drop_duplicates()
    files = files.drop_duplicates()
    # Delete non-numeric columns
    classes = classes.drop(["ID", "Name", "LongName", "Parent", "Component", "Path"], axis=1)
    files = files.drop(["ID", "Name", "LongName", "Parent"], axis=1)
    # Write whole processed project into 1 file
    classes.to_csv(data_output + project+'_classes.csv', index=False)
