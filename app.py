#!/usr/bin/env python

from flask import Flask, jsonify, render_template, json
import MySQLdb, MySQLdb.cursors

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')
    #return render_template('index.html', data=1981)

@app.route('/test')
def test():
    return render_template('test.html')
    #return render_template('index.html', data=1981)

@app.route('/data', methods=['GET'])
def data_func():
    conn = MySQLdb.connect(user="root", passwd = "", db="carsdb", cursorclass=MySQLdb.cursors.DictCursor)
    cur = conn.cursor()

    #http://stackoverflow.com/questions/7124418/mysql-subquery-limit
    #change url to date!!!
    cmd = "SELECT * FROM wdelta WHERE url in (SELECT * FROM (SELECT url FROM wdelta WHERE model in ('accord', 'civic', 'camry') ORDER BY rand() LIMIT 80) as t) ORDER BY delta DESC;"
    cur.execute(cmd)
    data = cur.fetchall()
    return jsonify(items=list(data))




if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    #port = int(os.environ.get('PORT', 5000))
    #app.debug = True
    #app.run(host='0.0.0.0', port=port)
    app.run(debug=True)
