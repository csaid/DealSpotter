#!/usr/bin/env python

from flask import Flask
from flask import render_template

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/test')
def test():
    return render_template('test.html',
                           my_name="George",
                           my_locations=[3, 4, 5, 6, 7, 8, 9, 10])



if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    #port = int(os.environ.get('PORT', 5000))
    #app.debug = True
    #app.run(host='0.0.0.0', port=port)
    app.run()
