import MySQLdb
import MySQLdb.cursors
from pandas import DataFrame, Series
import pandas as pd
import pandas.io.sql as sql
import numpy as np
from os import sys
import json
from sklearn.ensemble import RandomForestRegressor
import matplotlib.pyplot as plt
import utilities
reload(utilities)
import utilities as ut
from scipy.optimize import curve_fit


def get_mae(prediction, target):
    '''Mean Absolute Error'''
    return np.abs(prediction - target).mean()


def exp_func(x, a, b, c, d):
    '''Sum of two exponentials'''
    return a * np.exp(-b * (x[0])) + c * np.exp(-d * x[1])


def exp_func_score(features, target, train_idcs, test_idcs):
    '''Get Mean Absolute Error of sum of two exponentials function'''
    mile_scale = 2000  # Helps fitting search
    X = np.transpose(np.array(features))
    y = np.array(target)
    X[0,:] = 2014 - X[0,:] #Convert year to age
    X[1,:] = X[1,:] / mile_scale
    popt, pcov = curve_fit(
        exp_func, X[:, train_idcs], y[train_idcs], maxfev=50000)
    pred = exp_func(X[:, test_idcs], *popt)
    mae = get_mae(pred, y[test_idcs])

    return mae


def color_plot(predictor):
    '''Plots predicted price as function of year and mileage'''
    features = []
    miles = np.linspace(10000, 200000, 100)
    years = np.arange(1995, 2014)
    for mile in miles:
        for year in years:
            features.append([year, mile])
    features = np.array(features)
    prediction = np.array(predictor.predict(features))
    prediction = np.flipud(prediction.reshape((len(miles), len(years))))
    fig = plt.figure()
    plt.imshow(prediction, interpolation="nearest", aspect='auto')
    plt.show()
    fig.savefig('color.eps')


def line_plot(predictor):
    '''Plots predicted price as function of year'''
    fig = plt.figure()
    years = np.arange(1995, 2014)
    data = np.array([[year, 30000] for year in years])
    prediction = np.array(predictor.predict(data))
    plt.plot(years, prediction)
    plt.show()
    fig.savefig('line.eps')


def exclude_uni_outliers(df, name, mn, mx):
    '''
    Excludes univariate outliers
    Args:
        df - DataFrame
        name - column name (string)
        mn - minimum value to pass
        mx - maximum value to pass
    '''
    df = df.ix[df[name] >= mn,:]
    df = df.ix[df[name] <= mx,:]
    df.index = range(len(df))
    return df


def exclude_biv_outliers(df, x, y):
    '''Excludes bivariate outliers in year/mileage relationship'''

    group = df.groupby(by=['year'])

    valid = [False for i in range(len(df))]
    for i in range(len(df)):
        year = df.ix[i, x]
        miles = df.ix[i, y]
        mn = group.mean().ix[year, y] - 1.6 * group.std().ix[year, y]
        mx = group.mean().ix[year, y] + 1.6 * group.std().ix[year, y]
        if (miles < mx and miles > mn):
            valid[i] = True
    df = df[valid]
    return df


def make_unicode(s):
    return unicode(s, 'utf-8', errors='ignore')


def main():

    # Select all cars of desired models from database
    models = {'accord', 'camry', 'civic', 'corolla'}
    conn = MySQLdb.connect(
        user="root",
        passwd="",
        db="carsdb",
        cursorclass=MySQLdb.cursors.DictCursor)
    read_table_name = "scraped"
    cmd = "SELECT model, year, miles, price, url, body, title, date FROM " + \
        read_table_name + \
        " WHERE area='sfbay' AND model in " + str(tuple(models))
    full = pd.io.sql.read_frame(cmd, conn)

    # UTF-8 encoding
    full['body'] = full['body'].apply(make_unicode)
    full['title'] = full['title'].apply(make_unicode)

    # Exclude outliers
    full = exclude_uni_outliers(full, 'year', 1996, 2013)
    full = exclude_uni_outliers(full, 'miles', 1000, 210000)
    full = exclude_uni_outliers(full, 'price', 1000, 50000)
    full = exclude_biv_outliers(full, 'year', 'miles')

    # Only show most recent posts on DealSpotter
    full = full.sort('date', ascending=False)
    num_on_web = 150
    full['on_web'] = [True if i <
                      num_on_web else False for i in range(0, len(full))]

    # Initialize DataFrame to keep track of savings
    delta_frame = DataFrame(columns=['url', 'delta'])

    # Loop through models (accord, camry, etc) and grow delta_frame
    for i, model in enumerate(models):
        print(model)

        # This model's subset of full dataframe
        df = full[full['model'] == model]
        df = df[['price', 'year', 'miles', 'url', 'date', 'on_web']]
        on_web = df['on_web']  # keep track of indices
        not_on_web = df['on_web'] == False  # keep track of indices

        # All training should be on cars not shown on DealSpotter
        feature_names = ['year', 'miles']
        features = df.ix[not_on_web, feature_names].values
        target = df.ix[not_on_web, 'price'].values

        predictor = RandomForestRegressor(
            n_estimators=100,
            min_samples_split=20)

        # If user just wants to do cross-validation on training data
        if sys.argv[1] == 'xval':
            # Exclude true test cases from cross-validation
            (train_idcs, test_idcs) = ut.get_xval_indcs(len(features), .8)
            predictor.fit(features[train_idcs,:], target[train_idcs])
            predictions = np.array(predictor.predict(features[test_idcs,:]))
            print('MAE = ' + str(get_mae(predictions, target[test_idcs])))

        # If user wants to make predictions for real test cars, shown on DealSpotter
        elif sys.argv[1] == 'real':

            # Extract true test data for DealSpotter
            web_features = df.ix[on_web, feature_names].values
            web_target = df.ix[on_web, 'price'].values

            # Fit model, make predictions
            predictor.fit(features, target)
            predictions = np.array(predictor.predict(web_features))
            delta = predictions - web_target
            model_delta_frame = DataFrame(
                {'url': df.ix[on_web, 'url'].values, 'delta': delta})
            delta_frame = delta_frame.append(model_delta_frame)

        else:
            raise ValueError("Please provide 'xval' or 'real'")

    # If user wants to make predictions for real test cars, shown on DealSpotter
    if sys.argv[1] == 'real':
        print(delta_frame)

        # Merge savings information with original data frame
        full = full.merge(delta_frame, on='url', how='inner')

        # Write to database
        write_table_name = 'priced'
        ut.drop_if_exists(conn, write_table_name)
        ut.prepare_table_w_textcols(
            full, write_table_name, conn, ['body', 'title'])
        pd.io.sql.write_frame(
            full,
            write_table_name,
            conn,
            flavor="mysql",
            if_exists="append")




if __name__ == "__main__":
    main()
