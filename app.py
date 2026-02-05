from flask import Flask, render_template,url_for
import pandas as pd
app = Flask(__name__)

@app.route('/')
def index():
    df = pd.read_csv('data/banco.csv')
    return render_template('index.html',produtos=df.to_dict('records'))

if __name__ == '__main__':
    app.run(debug=True)