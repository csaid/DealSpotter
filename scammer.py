import MySQLdb
from pandas import DataFrame, Series
import pandas as pd
import numpy as np
from os import sys
import json
from sklearn.ensemble import RandomForestClassifier
import matplotlib.pyplot as plt
import utilities
reload(utilities)
import utilities as ut

def word_count(s):
    return len (s.split(" "))

def savings_percent(frame):
    return frame['delta']/frame['price']

def is_declared_dealer(s):
    return df.ix[1,'url'].split('/')[2]=='ctd'


INCLUDE HAS PHONE!!


def main():

    models = {model['name'] for model in json.load(open("models.json"))}
    show_models = {'accord', 'camry', 'civic'}
    conn = MySQLdb.connect(user="root", passwd = "", db="carsdb", cursorclass=MySQLdb.cursors.DictCursor)
    read_table_name = "wdelta"

    df = pd.io.sql.read_frame("SELECT * FROM " + read_table_name, conn)

    df['word_count'] = df['body'].apply(word_count)
    df['savings_percent'] = df[['delta', 'price']].apply(savings_percent, axis=1)
    df['is_declared_dealer'] = df['url'].apply(is_declared_dealer)



    feature_names = ['image_count', 'delta', 'price', 'word_count', 'savings_percent']
    features = df[feature_names].values
    target = df['is_flagged'].values

    predictor = RandomForestClassifier(n_estimators=300, min_samples_split=20)

    if sys.argv[1]=='xval':
        (train_idcs, test_idcs) = ut.get_xval_indcs(len(df), .7)
        predictor.fit(features[train_idcs,:], target[train_idcs])
        predictions = np.array(predictor.predict(features[test_idcs,:]))
        print(predictor.score(features[test_idcs,:], target[test_idcs]))


    elif sys.argv[1]=='real':
        predictor.fit(features, target)
        predictions = np.array(predictor.predict(features))
        delta = predictions - target
        model_delta_frame = DataFrame({'url':df['url'].values, 'delta':delta})
        delta_frame = delta_frame.append(model_delta_frame)

    else:
        raise ValueError("Please provide 'xval' or 'real'")


#  if sys.argv[1]=='real':
#        print(delta_frame)
#        write_table_name = 'ready'
#        ut.drop_if_exists(conn, write_table_name)
#        full = full.merge(delta_frame, on='url', how='inner')
#        ut.prepare_table_w_textcols(full, write_table_name, conn, ['body', 'title'])
#        pd.io.sql.write_frame(full, write_table_name, conn, flavor="mysql", if_exists="append")





if __name__ == "__main__":
    main()
