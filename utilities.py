import pandas as pd
import numpy as np
import re

def get_xval_indcs(n, training_frac):
    training_n = round(training_frac*n)
    data_idcs = np.random.permutation(range(0,n-1))
    training_idcs = data_idcs[:training_n]
    testing_idcs = data_idcs[training_n:]

    return training_idcs, testing_idcs

def drop_if_exists(conn, table_name):
    if pd.io.sql.table_exists(table_name, conn, flavor="mysql"):
        pd.io.sql.uquery("DROP TABLE " + table_name, conn)

def prepare_table_w_textcols(df, table_name, conn, text_columns):

    cmd = pd.io.sql.get_schema(df, table_name, 'mysql')

    for col in text_columns:
        cmd = re.sub(r"`" + col + "` VARCHAR \(63\)", r"`" + col + "` TEXT", cmd)

    pd.io.sql.execute(cmd, conn)
