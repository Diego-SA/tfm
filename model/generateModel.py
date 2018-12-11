import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.model_selection import cross_val_score
from sklearn.ensemble import RandomForestClassifier
import pickle

from sklearn.metrics import accuracy_score
from sklearn.metrics import precision_score
from sklearn.metrics import recall_score
from sklearn.metrics import f1_score
from sklearn.metrics import roc_auc_score

input_data = "../datasets/dataframes/"

print("Reading data")

# Classes dataframe
classes_df = pd.read_csv(input_data + "classes.csv")

classes_df_nobug = classes_df[classes_df['Number of bugs'] == 0]
classes_df_bug = classes_df[classes_df['Number of bugs'] > 0]

# Get same buggy and non-buggy files and shuffle it
muestra = 1000
classes_df = classes_df_nobug.sample(muestra).append(classes_df_bug.sample(muestra)).sample(frac=1)

# Separate attributes and label
classes_df_atts = classes_df.drop('Number of bugs', axis = 1)
classes_df_label = classes_df['Number of bugs'] > 0

# Train-Test split
X_train, X_test, y_train, y_test = train_test_split( classes_df_atts, classes_df_label, test_size=0.33, random_state=3)


print("Creating Random Forest Classifier")
# Basic classificator
clf = RandomForestClassifier(n_estimators=100, max_depth=2, random_state=0)

# Train classifier
clf.fit(X_train, y_train)

# Predict test set
prediction = clf.predict(X_test)

# Calculate different metrics
print('Metrics:')
print('Accuracy:', accuracy_score(y_test,prediction))
print('Precision: ', precision_score(y_test,prediction))
print('Recall: ', recall_score(y_test,prediction))
print('F-1 Score: ', f1_score(y_test,prediction))
print('Area Under Curve: ', roc_auc_score(y_test,prediction))

# Save in a Python object, so it can be used in future without classifing again
print("Saving classifier")
model_name = 'RandomForestv1.sav'
pickle.dump(clf, open(model_name, 'wb'))
