#!/usr/bin/env python

from flask import Flask, jsonify, render_template
import MySQLdb
import MySQLdb.cursors

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/slides')
def about():
    return render_template('slides.html')

@app.route('/data', methods=['GET'])
def data_func():
    conn = MySQLdb.connect(
        user="root",
        passwd="",
        db="carsdb",
        cursorclass=MySQLdb.cursors.DictCursor)
    cur = conn.cursor()
    cmd = "SELECT * FROM priced WHERE date in (SELECT * FROM (SELECT date FROM priced WHERE model in ('accord', 'civic', 'camry', 'corolla') ORDER BY date) as t) ORDER BY delta DESC;"

    cur.execute(cmd)
    data = cur.fetchall()
    return jsonify(items=list(data))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

