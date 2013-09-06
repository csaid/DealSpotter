#!/usr/bin/env python

from flask import Flask, jsonify, render_template, json
import MySQLdb, MySQLdb.cursors

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')
    #return render_template('index.html', data=1981)


@app.route('/data', methods=['GET'])
def data_func():
    conn = MySQLdb.connect(user="root", passwd = "", db="carsdb", cursorclass=MySQLdb.cursors.DictCursor)
    cur = conn.cursor()
    cur.execute("SELECT * FROM cars WHERE price > 1000 AND miles > 1000 ORDER BY delta")
    data = cur.fetchall()
    return jsonify(items=list(data))




if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    #port = int(os.environ.get('PORT', 5000))
    #app.debug = True
    #app.run(host='0.0.0.0', port=port)
    app.run(debug=True)
