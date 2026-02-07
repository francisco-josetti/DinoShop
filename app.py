from flask import Flask, render_template,url_for, redirect, request, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import sqlite3
import pandas as pd
from werkzeug.security import generate_password_hash, check_password_hash
app = Flask(__name__)

app.config['SECRET_KEY'] = 'mysecretkey'
class User(UserMixin):
    def __init__(self,email):
        self.id = id
        self.email = email

login_manager = LoginManager()
login_manager.init_app(app)

def init_db():
    connect = sqlite3.connect('data/dados.db')
    cursor = connect.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS dados (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, email TEXT NOT NULL UNIQUE, senha TEXT NOT NULL)')
    cursor.execute('CREATE TABLE IF NOT EXISTS produtos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, preco REAL NOT NULL, descricao TEXT NOT NULL, imagem TEXT NOT NULL, usuario_id INTEGER NOT NULL, FOREIGN KEY (usuario_id) REFERENCES dados (id) ON DELETE CASCADE)')
    connect.commit()
    connect.close()

@app.route('/')
def index():
    connect = sqlite3.connect('data/dados.db')
    connect.row_factory = sqlite3.Row
    cursor = connect.cursor()
    cursor.execute('SELECT * FROM produtos')
    produtos = cursor.fetchall()
    connect.close()
    return render_template('index.html',produtos=produtos, user=current_user)

@app.route('/cadastro',methods=['GET','POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        senha_criptografada = generate_password_hash(senha)
        connect = sqlite3.connect('data/dados.db')
        cursor = connect.cursor()
        cursor.execute('INSERT INTO dados (nome,email,senha) VALUES (?,?,?)',(nome,email,senha_criptografada))
        connect.commit()
        connect.close()
        user = User(email)
        login_user(user)
        return redirect(url_for('index'))
    return render_template('cadastro.html')

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        connect = sqlite3.connect('data/dados.db')
        cursor = connect.cursor()
        cursor.execute('SELECT * FROM dados WHERE email=?',(email,))
        user = cursor.fetchone()
        connect.close()
        if user:
            if check_password_hash(user['senha'],senha):
                user = User(user['email'])
                login_user(user)
                return redirect(url_for('index'))
            else:
                flash('Email ou senha incorretos')
                return redirect(url_for('login'))

@app.route('/descricao/<int:id>')
def descricao(id):
    connect = sqlite3.connect('data/dados.db')
    connect.row_factory = sqlite3.Row
    cursor = connect.cursor()
    cursor.execute('SELECT * FROM produtos WHERE id=?',(id,))
    produto = cursor.fetchone()
    connect.close()
    return render_template('descricao_produto.html',produto=produto)

@app.route('/pesquisa',methods=['GET'])
def pesquisa():
    pesquisa = request.args.get('pesquisa')
    connect = sqlite3.connect('data/dados.db')
    connect.row_factory = sqlite3.Row
    cursor = connect.cursor()
    cursor.execute('SELECT * FROM produtos WHERE nome LIKE ?',(f'%{pesquisa}%',))
    produtos = cursor.fetchall()
    connect.close()
    return render_template('index.html',produtos=produtos, user=current_user)

@app.route('/adicionar-carrinho/<int:id>')
def adicionar_carrinho(id):
    connect = sqlite3.connect('data/dados.db')
    cursor = connect.cursor()
    cursor.execute('SELECT * FROM produtos WHERE id=?',(id,))
    produto = cursor.fetchone()
    connect.close()
    return render_template('descricao_produto.html',produto=produto)
    
@login_manager.user_loader
def load_user(user_id):
    if user_id is None:
        return None
    return User(user_id)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)