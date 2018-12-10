# -*- coding: utf-8 -*-
"""
Created on Thu Dec  6 14:32:20 2018

@author: Diego
"""

import pandas as pd
import os
import pickle

project_name = 'java-design-patterns'
data_dir = 'Results/' + project_name + '/java'

train_dir = "../datasets/dataframes/"

last_analysis = sorted(os.listdir(data_dir), reverse = True)[0]

class_df = None
for file in os.listdir(data_dir + '/' + last_analysis):
    if (len(file) > 10 and file[-10:] == '-Class.csv'):
        class_df = pd.read_csv(data_dir + "/" + last_analysis + "/" + file, sep = ',')
        print(data_dir + "/" + last_analysis + "/" + file)
        break

# Delete non-numeric attributes, and attributes wich doesn't appear in train data
class_df = class_df.set_index("ID")

prediction_df = class_df.drop(['Name', 'LongName', 'Parent', 'Component', 'Path', 'Runtime Rules'], axis = 1)
print(prediction_df)
classifier_dir = 'RandomForestv1.sav'
# Load classifier and predict
clf = pickle.load(open(classifier_dir, 'rb'))

prediction = clf.predict(prediction_df)

for idx, predict in zip(prediction_df.index, prediction):
    if (predict):
        print("File " + class_df.loc[idx, 'Name'] + " probably has bugs")
    else:
        print("File " + class_df.loc[idx, 'Name'] + " probably hasn't bugs")