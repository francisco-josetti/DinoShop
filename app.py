from flask import Flask, render_template,url_for, redirect, request, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import pandas as pd
app = Flask(__name__)

app.config['SECRET_KEY'] = 'mysecretkey'
class User(UserMixin):
    def __init__(self,email):
        self.id = email

login_manager = LoginManager()
login_manager.init_app(app)
@app.route('/')
def index():
    df = pd.read_csv('data/banco.csv')
    return render_template('index.html',produtos=df.to_dict('records'),current_user=current_user)

@app.route('/cadastro',methods=['GET','POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        df = pd.read_csv('data/dados.csv')
        if email not in df['email'].astype(str).tolist():
            if len(df) == 0:
                df = pd.concat([df,pd.DataFrame({"id":[0],"nome":[nome],"email":[email],"senha":[senha]})],ignore_index=True)
            else:
                df = pd.concat([df,pd.DataFrame({"id":[df['id'].max() + 1],"nome":[nome],"email":[email],"senha":[senha]})],ignore_index=True)
            df.to_csv('data/dados.csv',index=False)
            user = User(email=email)
            login_user(user)
            return redirect(url_for('index'))
    else:
        flash('Email já cadastrado')
        return render_template('cadastro.html')
    return render_template('cadastro.html')

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        df = pd.read_csv('data/dados.csv')
        usuario_df = df[df['email'] == email]
        if not usuario_df.empty and str(usuario_df.iloc[0]['senha']) == str(senha):
            user = User(email)
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Credenciais inválidas')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/descricao/<int:id>')
def descricao(id):
    df = pd.read_csv('data/banco.csv')
    produto = df[df['id'] == id].to_dict('records')[0]
    return render_template('descricao_produto.html',produto=produto)
@login_manager.user_loader
def load_user(user_id):
    if user_id is None:
        return None
    return User(user_id)

if __name__ == '__main__':
    app.run(debug=True)