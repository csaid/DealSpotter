from bs4 import BeautifulSoup
import urllib2
import re
import pickle
import time
import MySQLdb
import json
from pandas import DataFrame, Series
import pandas as pd
import numpy as np
from os import sys
from sklearn.ensemble import RandomForestRegressor
import matplotlib.pyplot as plt


def dummy_code_model(df, models):
    for model in models:
        df['is_' + model] = (df['model']==model)
    df = df.drop('model', 1)

    return df

def color_plot(predictor):
    features = []
    miles = range(10000, 200000, 5000)
    years = range(1995, 2013)
    for mile in miles:
        for year in years:
            features.append([True, False, False, mile, year, False]) #MAY CAUSE ERRORS BECAUSE ORDER OF FEATURES ISN'T GUARANTEED.
    features = np.array(features)
    prediction = np.array(predictor.predict(features))
    prediction = prediction.reshape((len(miles), len(years)))
    plt.figure()
    plt.imshow(prediction, interpolation="nearest")


def main():

    models = ('accord', 'civic', 'camry', 'corolla')
    conn = MySQLdb.connect(user="root", passwd = "", db="carsdb", cursorclass=MySQLdb.cursors.DictCursor)
    table_name = "train"
    cmd = "SELECT * FROM " + table_name + " WHERE price > 1000 AND miles > 1000 and model in " + str(models)
    df = pd.io.sql.read_frame(cmd, conn)

    df = df[['price', 'model', 'year', 'miles']]
    df = dummy_code_model(df, models)

    feature_names = set(df.columns)
    feature_names.remove('price')
    feature_names = list(feature_names)

    features = df[feature_names].values
    target = df['price'].values

    predictor = RandomForestRegressor(n_estimators=100, n_jobs=-1, compute_importances = True)
    predictor.fit(features, target)
    predictions = np.array(predictor.predict(features))



if __name__ == "__main__":
    main()
