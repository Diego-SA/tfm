import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.model_selection import cross_val_score
from sklearn.ensemble import RandomForestClassifier
import pickle

input_data = "../datasets/dataframes/"

print("Reading data")

# Classes dataframe
classes_df = pd.read_csv(input_data + "classes.csv")

classes_df_nobug = classes_df[classes_df['Number of bugs'] == 0]
classes_df_bug = classes_df[classes_df['Number of bugs'] > 0]

# Get same buggy and non-buggy files and shuffle it
muestra = 1000
classes_df_partial = classes_df_nobug.sample(muestra).append(classes_df_bug.sample(muestra)).sample(frac=1)

# Attributes
classes_atts = classes_df_partial.drop("Number of bugs", axis = 1)
# Class: Buggy vs. Non-buggy files. Number of bugs is unnecesary for the moment
classes_label = classes_df_partial["Number of bugs"] > 0

print("Creating Random Forest Classifier")
# Basic classificator
clf = RandomForestClassifier(n_estimators=100, max_depth=2, random_state=0)

print("Cross validation")
# Cross-validation scores, for checking in model can predict something
print(cross_val_score(clf, classes_atts, classes_label, cv = 5))

# Train classifier
clf.fit(classes_atts, classes_label)

# Save in a Python object, so it can be used in future without classifing again
print("Saving classifier")
model_name = 'RandomForestv1.sav'
pickle.dump(clf, open(model_name, 'wb'))
