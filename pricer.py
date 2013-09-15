import MySQLdb
from pandas import DataFrame, Series
import pandas as pd
import numpy as np
from os import sys
import json
from sklearn.ensemble import RandomForestRegressor
import matplotlib.pyplot as plt
import utilities
reload(utilities)
import utilities as ut


def color_plot(predictor):
    features = []
    miles = np.arange(10000, 200000, 2000)
    years = np.arange(1995, 2013, .5)
    for mile in miles:
        for year in years:
            features.append([year, mile])
    features = np.array(features)
    prediction = np.array(predictor.predict(features))
    prediction = prediction.reshape((len(miles), len(years)))
    plt.figure()
    plt.imshow(prediction, interpolation="nearest")
    plt.show()

def exclude_uni_outliers(df, name, mn, mx):
    df = df.ix[df[name]>=mn,:]
    df = df.ix[df[name]<=mx,:]
    df.index = range(len(df))
    return df

def exclude_biv_outliers(df, x, y):
    group = df.groupby(by=['year'])

    valid = [False for i in range(len(df))]
    for i in range(len(df)):
        year = df.ix[i, x]
        miles = df.ix[i, y]
        mn = group.mean().ix[year, y] - 1.6*group.std().ix[year, y]
        mx = group.mean().ix[year, y] + 1.6*group.std().ix[year, y]
        if (miles < mx and miles > mn):
            valid[i] = True
    df = df[valid]
    return df

def main():

    models = {model['name'] for model in json.load(open("models.json"))}
    show_models = {'accord', 'camry', 'civic'}
    conn = MySQLdb.connect(user="root", passwd = "", db="carsdb", cursorclass=MySQLdb.cursors.DictCursor)
    read_table_name = "scraped"

    full = pd.io.sql.read_frame("SELECT * FROM " + read_table_name, conn)
    full = exclude_uni_outliers(full, 'year', 1996, 2013)
    full = exclude_uni_outliers(full, 'miles', 1000, 250000)
    full = exclude_uni_outliers(full, 'price', 1000, 50000)
    full = exclude_biv_outliers(full, 'year', 'miles')



    delta_frame = DataFrame(columns=['url', 'delta'])

    for i, model in enumerate(models):
        df = full[full['model']==model]

        if len(df) > 30: #don't bother analyzing small n models
            print(model)
            df = df[['price', 'year', 'miles', 'url']]

            feature_names = ['year', 'miles']
            features = df[feature_names].values
            target = df['price'].values

            predictor = RandomForestRegressor(n_estimators=300, min_samples_split=20)

            if sys.argv[1]=='xval':
                (train_idcs, test_idcs) = ut.get_xval_indcs(len(df), .8)
                predictor.fit(features[train_idcs,:], target[train_idcs])
                predictions = np.array(predictor.predict(features[test_idcs,:]))
                print(predictor.score(features[test_idcs,:], target[test_idcs]))
                if model in show_models:
                    color_plot(predictor)

            elif sys.argv[1]=='real':
                predictor.fit(features, target)
                predictions = np.array(predictor.predict(features))
                delta = predictions - target
                model_delta_frame = DataFrame({'url':df['url'].values, 'delta':delta})
                delta_frame = delta_frame.append(model_delta_frame)

            else:
                raise ValueError("Please provide 'xval' or 'real'")


    if sys.argv[1]=='real':
        print(delta_frame)
        write_table_name = 'wdelta'
        ut.drop_if_exists(conn, write_table_name)
        full = full.merge(delta_frame, on='url', how='inner')
        ut.prepare_table_w_textcols(full, write_table_name, conn, ['body', 'title'])
        pd.io.sql.write_frame(full, write_table_name, conn, flavor="mysql", if_exists="append")





if __name__ == "__main__":
    main()
