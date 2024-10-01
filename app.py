from flask import Flask, render_template, request, redirect, url_for, session
from dao.db import get_db_connection

app = Flask(__name__)
app.secret_key = 'your_secret_key'

#rota do site
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/logar', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_user = request.form['loginUser'] #Captura os dados enviados no formulário de login
        senha = request.form['senha']
        
        conn = get_db_connection()
        try:
            cur = conn.cursor() #Executa a consulta SQL para verificar se o login e senha existem no banco.
            cur.execute('SELECT * FROM users WHERE loginUser = %s AND senha = %s', (login_user, senha))
            user = cur.fetchone() #Retorna o primeiro resultado encontrado.
        finally:
            cur.close()
            conn.close()
        
        if user:
            session['loginUser'] = login_user #Armazena as informações de login e tipo de usuário na sessão.
            session['tipoUser'] = user[2]
            return redirect(url_for('home'))
        else:
            return 'Credenciais inválidas'
    
    return render_template('login.html')


@app.route('/cadastrar', methods=['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        login_user = request.form['loginUser']
        senha = request.form['senha']
        tipo_user = request.form['tipoUser']
        
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute('INSERT INTO users (loginUser, senha, tipoUser) VALUES (%s, %s, %s)', (login_user, senha, tipo_user))
            conn.commit() #Confirma a inserção no banco de dados.
        finally:
            cur.close()
            conn.close()
        
        return redirect(url_for('home'))
    
    return render_template('register_user.html')

@app.route('/cadastrar/produto', methods=['GET', 'POST'])
def register_product():
    if 'loginUser' not in session: #Verifica se o usuário está logado
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        nome = request.form['nome']
        qtde = request.form['qtde']
        preco = request.form['preco']
        login_user = session['loginUser']
        
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute('SELECT COUNT(*) FROM produtos WHERE loginUser = %s', (login_user,))
            count = cur.fetchone()[0]
            
            cur.execute('SELECT tipoUser FROM users WHERE loginUser = %s', (login_user,))
            user_type = cur.fetchone()[0]
            
            if user_type == 'normal' and count >= 3:
                return 'Você atingiu o limite de produtos!'
            
            cur.execute('INSERT INTO produtos (nome, loginUser, qtde, preco) VALUES (%s, %s, %s, %s)', (nome, login_user, qtde, preco))
            conn.commit()
        finally:
            cur.close()
            conn.close()
        
    
    return render_template('register_product.html')

@app.route('/produtos')
def listar_produtos():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT nome, qtde, preco FROM produtos;")
    produtos = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('list_products.html', produtos=produtos)

@app.route('/logout')
def logout():
    #Faz logout do usuário e redireciona para a página de login.
    session.pop('loginUser', None)
    session.pop('tipoUser', None)
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)

