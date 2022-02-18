from flask import Flask

app = Flask(__name__)


@app.route('/')
def index():
    return 'Index Page'
@app.route('/hello/<username>')
def hello(username):  # put application's code here
    return 'Hello World!%s'% username


if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0')
