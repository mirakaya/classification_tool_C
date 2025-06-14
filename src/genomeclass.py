import argparse
import pickle
import subprocess
import time
import os
import warnings

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import numpy as np
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score, average_precision_score
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import LabelEncoder, label_binarize
from xgboost import XGBClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier

from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
import matplotlib.pyplot as plt
from collections import Counter



def import_files(filename):  # import the csv file

	chunks = pd.read_csv(filename, sep='\t', low_memory=False, chunksize=500000)
	data = pd.concat(chunks, ignore_index=True)

	#print(data)

	return data


def print_info(data):  # prints data information

	# check dimensions
	data.shape

	# check the info on the columns - no null values
	data.info()

	# Summary of the numerical attributes
	data.describe()


def correlation(data):
	# Delete less relevant features based on the correlation with the output variable
	data_copy = data
	data_copy.drop("Sequence id", axis=1, inplace=True)
	cor = data_copy.corr()  # calculate correlations

	sns.set(font_scale=1.3)

	# Correlation graph
	plt.figure(figsize=(22, 22))
	sns.heatmap(cor, annot=True, cmap=sns.diverging_palette(20, 220, n=200), vmin=-1, vmax=1)
	plt.savefig('correlation.pdf')
	plt.savefig('correlation.jpg')
	plt.show()


# Correlation with output variable
# list_columns_dropped = remove_low_correlation(data, cor_target)

# return list_columns_dropped




def drop_columns(data):
	le = LabelEncoder()
	X = data.drop(columns=['Sequence_id'])
	y = le.fit_transform(data['Sequence_id'])

	print(f"Class 8 label: {le.inverse_transform([8])[0]}")

	return X, y


def print_to_files(info):
	f_tex = open("performance_model.tex", "a")
	f_tsv = open("performance_model.tsv", "a")

	for elem in info:
		i = str(elem)
		f_tex.write(i + " & ")
		f_tsv.write(i + "\t")
	f_tex.write("\\\\\\hline\n")
	f_tsv.write("\n")

	f_tex.close()
	f_tsv.close()


def cross_validation_MLPRegressor(X_train, y_train, y_test):
	param_activation = ['tanh', 'relu']
	param_solver = ['sgd', 'adam']
	param_alpha = [0.0001, 0.001, 0.01, 0.1]
	param_learning_rate = ['constant', 'adaptive']
	param_hidden_layer_sizes = [(50, 50, 50), (50, 100, 50), (100,), (5, 5, 5), (50, 50), (5, 5), (2, 5, 2)]

	for activation in param_activation:

		for solver in param_solver:

			for alpha in param_alpha:

				for learning_rate in param_learning_rate:

					for hidden_layer_sizes in param_hidden_layer_sizes:
						model = MLPRegressor(hidden_layer_sizes=hidden_layer_sizes, activation=activation,
											 solver=solver, alpha=alpha, learning_rate=learning_rate, random_state=42)

						model.fit(X_train, y_train)
						y_pred = model.predict(X_test)

						# Evaluate the model's performance
						mse = mean_squared_error(y_test, y_pred)
						r2 = r2_score(y_test, y_pred)
						mae = mean_absolute_error(y_test, y_pred)
						mape = mean_absolute_percentage_error(y_test, y_pred)
						print(hidden_layer_sizes, activation, solver, alpha, learning_rate)
						print(f"Mean squared error: {mse:.2f}")
						print(f"R-squared: {r2:.2f}")
						print(f"Mean absolute error: {mae:.2f}")
						print(f"Mean absolute percentage error: {mape:.2f}")

						info = [hidden_layer_sizes, activation, solver, alpha, learning_rate, mse, r2, mae, mape]

						print_to_files(info)


def cross_validation_MLPRegressor_v2(X_train, y_train, y_test):
	param_grid = {
		'hidden_layer_sizes': [(20,), (15, 30), (15, 15), (10,), (10, 10), (20, 10), (10, 20), (20, 20)],
		# 'hidden_layer_sizes': [(20, 20), (20, 20, 20), (20, 20, 20, 20)],
		# 'hidden_layer_sizes': [(20,), (19,), (18,), (21,), (22,), (20, 5), (20, 20), (20, 30)],
		'activation': ['relu'],
		'solver': ['adam', 'sgd'],
		'alpha': [0.01, 0.005, 0.05],
		'learning_rate': ['constant', 'adaptive']
	}

	model = MLPRegressor(random_state=42)

	cv = GridSearchCV(model, param_grid, n_jobs=6, verbose=10, cv=3)
	cv.fit(X_train, y_train)
	print(cv.best_estimator_)
	print(cv.best_score_)
	print(cv.best_params_)

	return cv


def cross_validation_GradientBoostingRegression(X_train, y_train, y_test):
	param_grid = {
		'loss': ["squared_error", "absolute_error"],
		'learning_rate': [0.1, 0.2, 0.3],
		'criterion': ["friedman_mse"],
		'n_estimators': [15, 30, 50],
		'min_samples_split': [2, 4]
	}

	model = GradientBoostingRegressor(random_state=42)

	cv = GridSearchCV(model, param_grid, n_jobs=6, verbose=10, cv=3)
	cv.fit(X_train, y_train)
	print(cv.best_estimator_)
	print(cv.best_score_)
	print(cv.best_params_)

	return cv


def cross_validation_NNR(X_train, y_train, y_test):
	param_grid = {
		'n_neighbors': [1, 3, 5, 7, 9, 15],
		'weights': ['uniform', 'distance'],
		'algorithm': ['brute', 'auto'],
	}

	model = KNeighborsRegressor()

	cv = GridSearchCV(model, param_grid, n_jobs=-1, verbose=10, cv=2, error_score='raise')
	cv.fit(X_train, y_train)
	print(cv.best_estimator_)
	print(cv.best_score_)
	print(cv.best_params_)

	return cv


def cross_validation_LinearRegression(X_train, y_train, y_test):
	param_grid = {
		'fit_intercept': [True, False],
		'n_jobs': [-1],
		'C': [1, 5, 10, 50, 100],
		'gamma': ["scale", "auto"]
	}

	model = LinearRegression(random_state=42)

	cv = GridSearchCV(model, param_grid, n_jobs=-1, verbose=1, cv=2)
	cv.fit(X_train, y_train)
	print(cv.best_estimator_)
	print(cv.best_score_)
	print(cv.best_params_)

	return cv


def generate_plots(data):
	data.hist(bins=50, figsize=(20, 15))
	plt.show()


def fit_and_predict(model, name, is_test):
	if is_test == True:
		# Print model name
		print("\n\nTesting the " + name + "...")

		# Optional: Check input columns
		#print(data.columns)

		# Train the model
		model.fit(X_train, y_train)

		# Make predictions
		y_pred = model.predict(X_test)
		y_scores = model.predict_proba(X_test)  # shape: (n_samples, n_classes)

		# Binarize true labels using only the model's classes
		y_test_bin = label_binarize(y_test, classes=model.classes_)

		# === Evaluate the model ===

		'''print("Unique classes in y_test:", set(y_test))
		print("y_scores shape:", y_scores.shape)
		print("y_test_bin shape:", y_test_bin.shape)
		print("Sample y_scores:", y_scores[:5])
		print("Variance of y_scores:", np.var(y_scores, axis=0))'''

		# Accuracy
		acc = accuracy_score(y_test, y_pred)

		# F1 Score (macro averages across classes)
		f1 = f1_score(y_test, y_pred, average='macro')

		# AUROC (macro-averaged across classes)
		auroc = roc_auc_score(y_test_bin, y_scores, multi_class='ovr', average='macro')

		# AUPRC (macro-averaged across classes)
		auprc = average_precision_score(y_test_bin, y_scores, average='macro')

		print("Class distribution in y_test:")
		print(Counter(y_test))

		cm = confusion_matrix(y_test, y_pred, labels=model.classes_)
		disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=model.classes_)
		disp.plot(xticks_rotation=45)
		plt.title("Confusion Matrix")
		plt.show()

		# Print results
		print(f"Accuracy: {acc:.4f}")
		print(f"F1 Score: {f1:.4f}")
		print(f"AUROC: {auroc:.4f}")
		print(f"AUPRC: {auprc:.4f}")

	else:
		print("Saving the " + name + "...")

		model.fit(X, Y)

		# save model
		filename = name + '.sav'
		pickle.dump(model, open(filename, 'wb'))


if __name__ == '__main__':

	warnings.filterwarnings("ignore")

	parser = argparse.ArgumentParser(description="Index", usage="Training and testing\n\npython3 genomeclass.py -f <input multi-FASTA file> -i <input (multi-)FASTA file>\n"
	                                                            "python3 genomeclass.py -t <input TSV file -i <input (multi-)FASTA file>\n")

	parser.add_argument("-f", help="Input multi-FASTA file", type=str)
	parser.add_argument("-t", help="Input TSV file", type=str)
	parser.add_argument("-i", help="Input FASTA file containing the sequences to be classified", nargs="+", type=str, required=False)
	parser.add_argument("-m", help="Machine learning model to be used. Default: RandomForestClassifier", type=str)
	parser.add_argument("-o", help="Options for the execution of the C file. Please surround the options with \"\"", type=str)

	args = parser.parse_args()

	if args.o != None:
		options = args.o
	else:
		options = "-s -g -c -e -m"

	if args.f is not None and os.path.exists(args.f):
		print("Using " + args.f + " as the input file. Running genomeclass...\n")
		#os.system("make clean")
		#os.system("make")
		#os.system("./genomeclass -i " + args.f + " " + options)
		dataset_name = "output.tsv"

	elif args.t is not None and os.path.exists(args.t):
		print("Using " + args.t[0] + "as the input file.\n")
		dataset_name = args.t

	else:
		print("No input file. Exiting.")
		exit(1)

	if args.i is not None:
		print("File to be classified: " + args.i[0] + "\n")
	else:
		print("No file to classify. Exiting.")
		exit(1)

	pd.set_option('display.max_columns', 30)

	file_tsv = "performance_genomeclass_testing.tsv"

	if os.path.exists(file_tsv):
		os.remove(file_tsv)

	data = import_files(dataset_name)

	print(data.dtypes)
	print(data.shape)

	X, Y = drop_columns(data)
	X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size=0.2, random_state=42)

	# get parameters
	# print("Starting MLPRegressor")
	# model_mlp = cross_validation_MLPRegressor_v2(X_train, y_train, X_test)

	# train and save models
	xgboost = XGBClassifier(random_state=42)
	fit_and_predict(xgboost, "XGBClassifier", True)

	gnb = GaussianNB()
	fit_and_predict(gnb, "GaussianNB", True)

	svc = SVC(probability=True, random_state=42)
	fit_and_predict(svc, "SVC", True)

	knn = KNeighborsClassifier()
	fit_and_predict(knn, "KNeighborsClassifier", True)

	rfc = RandomForestClassifier(random_state=42)
	fit_and_predict(rfc, "RandomForestClassifier", True)

	mlp = MLPClassifier(random_state=42)
	fit_and_predict(mlp, "MLPClassifier", True)

	#fit_and_predict(mlp_model, "mlp_model", False)

'''	gbr_model = GradientBoostingRegressor(learning_rate=0.3, min_samples_split=4, n_estimators=50, random_state=42)
	fit_and_predict(gbr_model, "gbr_model", True)
	fit_and_predict(gbr_model, "gbr_model", False)'''
