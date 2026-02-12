from flask import Flask, render_template,url_for, redirect, request, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import sqlite3
import pandas as pd
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.config['SECRET_KEY'] = 'mysecretkey'
class User(UserMixin):
    def __init__(self,id,nome, email,foto=None):
        self.id = id
        self.nome = nome
        self.email = email
        self.foto = foto

login_manager = LoginManager()
login_manager.init_app(app)

def init_db():
    connect = sqlite3.connect('data/dados.db')
    cursor = connect.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS dados (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, email TEXT NOT NULL UNIQUE, senha TEXT NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS produtos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, preco REAL NOT NULL, descricao TEXT NOT NULL, imagem TEXT NOT NULL, usuario_id INTEGER NOT NULL, quantidade INTEGER NOT NULL, FOREIGN KEY (usuario_id) REFERENCES dados (id) ON DELETE CASCADE)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS carrinho (id INTEGER PRIMARY KEY AUTOINCREMENT, produto_id INTEGER NOT NULL, usuario_id INTEGER NOT NULL, quantidade INTEGER NOT NULL, preco REAL NOT NULL, FOREIGN KEY (produto_id) REFERENCES produtos (id) ON DELETE CASCADE, FOREIGN KEY (usuario_id) REFERENCES dados (id) ON DELETE CASCADE)''')
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
        user_id = cursor.lastrowid
        connect.close()
        user = User(user_id, nome, email)
        login_user(user)
        return redirect(url_for('index'))
    return render_template('cadastro.html')

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        connect = sqlite3.connect('data/dados.db')
        connect.row_factory = sqlite3.Row
        cursor = connect.cursor()
        cursor.execute('SELECT * FROM dados WHERE email=?',(email,))
        user = cursor.fetchone()
        connect.close()
        if user:
            if check_password_hash(user['senha'],senha):
                user = User(user['id'],user['nome'],user['email'])
                login_user(user)
                return redirect(url_for('index'))
            else:
                flash('Email ou senha incorretos')
                return redirect(url_for('login'))
    else:
        return render_template('login.html')

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
    if current_user.is_authenticated:
        if request.method == 'GET':
            if request.args.get('quantidade'):
                quantidade = request.args.get('quantidade')
            else:
                quantidade = 1
            connect = sqlite3.connect('data/dados.db')
            cursor = connect.cursor()
            cursor.row_factory = sqlite3.Row
            cursor.execute('SELECT * FROM produtos WHERE id=?',(id,))
            produto = cursor.fetchone()
            if produto['quantidade'] >= int(quantidade):
                cursor.execute('INSERT INTO carrinho (produto_id,usuario_id,quantidade,preco,nome) VALUES (?,?,?,?,?)',(produto['id'],current_user.id,quantidade,produto['preco'],produto['nome']))
                connect.commit()
                connect.close()
                return render_template('descricao_produto.html',produto=produto)
@login_required
@app.route('/carrinho')
def carrinho():
    connect = sqlite3.connect('data/dados.db')
    connect.row_factory = sqlite3.Row
    cursor = connect.cursor()
    cursor.execute('SELECT * FROM carrinho WHERE usuario_id=?',(current_user.id,))
    produtos = cursor.fetchall()
    connect.close()
    return render_template('carrinho.html',produtos=produtos)
@app.route('/carrinho/remover/<int:id>')
def remover_carrinho(id):
    connect = sqlite3.connect('data/dados.db')
    cursor = connect.cursor()
    cursor.execute('DELETE FROM carrinho WHERE id=?',(id,))
    connect.commit()
    connect.close()
    return redirect(url_for('carrinho'))

@app.route('/carrinho/limpar-carrinho')
def limpar_carrinho():
    connect = sqlite3.connect('data/dados.db')
    cursor = connect.cursor()
    cursor.execute('DELETE FROM carrinho WHERE usuario_id=?',(current_user.id,))
    connect.commit()
    connect.close()
    return redirect(url_for('carrinho'))
@app.route('/conta')
@login_required
def conta():
    return render_template('conta.html',user=current_user)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@login_required
@app.route('/vender', methods=['GET', 'POST'])
def vender():
    if request.method == 'POST':
        nome = request.form['nome']
        preco = request.form['preco']
        descricao = request.form['descricao']
        quantidade = request.form['quantidade']
        imagem = request.files['imagem']
        imagem_salva = secure_filename(imagem.filename)
        imagem.save(os.path.join(app.config['UPLOAD_FOLDER'],imagem_salva))
        connect = sqlite3.connect('data/dados.db')
        cursor = connect.cursor()
        cursor.execute('INSERT INTO produtos (nome,preco,descricao,quantidade,imagem,usuario_id) VALUES (?,?,?,?,?,?)',(nome,preco,descricao,quantidade,imagem_salva,current_user.id))
        connect.commit()
        connect.close()
        return redirect(url_for('index'))
    return render_template('vender.html')

@login_required
@app.route('/editar-perfil', methods=['GET', 'POST'])
def editar_perfil():
    if request.method == 'POST':
        nome = request.form['nome']
        foto = request.files['foto']
        foto_salva = secure_filename(foto.filename)
        foto.save(os.path.join(app.config['UPLOAD_FOLDER'],foto_salva))
        connect = sqlite3.connect('data/dados.db')
        cursor = connect.cursor()
        cursor.execute('UPDATE dados SET nome=?,foto=? WHERE id=?', (nome, foto_salva, current_user.id))
        connect.commit()
        connect.close()
        return redirect(url_for('conta'))
    return render_template('editar_perfil.html', user=current_user)
@login_manager.user_loader
def load_user(user_id):
    connect = sqlite3.connect('data/dados.db')
    connect.row_factory = sqlite3.Row
    cursor = connect.cursor()
    cursor.execute('SELECT * FROM dados WHERE id=?', (user_id,))
    user = cursor.fetchone()
    connect.close()

    if user:
        return User(user['id'], user['nome'], user['email'], user['foto'])
    return None



if __name__ == '__main__':
    init_db()
    app.run(debug=True)