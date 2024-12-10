from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from dao.db import get_db_connection
import threds as thread
import pandas as pd
import plotly.express as px


app = Flask(__name__)
app.secret_key = 'your_secret_key'


# Rota do site
@app.route('/')
def home():
    return render_template('home.html')


@app.route('/logar', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_user = request.form['loginUser']  # Captura os dados enviados no formulário de login
        senha = request.form['senha']
        
        conn = get_db_connection()
        try:
            cur = conn.cursor()  # Executa a consulta SQL para verificar se o login e senha existem no banco.
            cur.execute('SELECT * FROM users WHERE loginUser = %s AND senha = %s', (login_user, senha))
            user = cur.fetchone()  # Retorna o primeiro resultado encontrado.
        finally:
            cur.close()
            conn.close()
        
        if user:
            session['loginUser'] = login_user  # Armazena as informações de login e tipo de usuário na sessão.
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
            comando = cur.execute('INSERT INTO users (loginUser, senha, tipoUser) VALUES (%s, %s, %s)', 
                                  (login_user, senha, tipo_user))
            thread.ThreadsExemplo(comando)
            conn.commit()  # Confirma a inserção no banco de dados.
        finally:
            cur.close()
            conn.close()
        
        return redirect(url_for('home'))
    
    return render_template('register_user.html')


@app.route('/cadastrar/produto', methods=['GET', 'POST'])
def register_product():
    if 'loginUser' not in session: 
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
    try:
        cur = conn.cursor()
        cur.execute('SELECT id, nome, qtde, preco FROM produtos')
        produtos = cur.fetchall()
    finally:
        cur.close()
        conn.close()

    return render_template('list_products.html', produtos=produtos)



@app.route('/logout')
def logout():
    # Faz logout do usuário e redireciona para a página de login.
    session.pop('loginUser', None)
    session.pop('tipoUser', None)
    return redirect(url_for('login'))


# API RESTful
@app.route('/api/produto', methods=['POST'])
def inserir_produto():
    data = request.get_json()  # Recebe os dados no formato JSON
    nome = data.get('nome')
    qtde = data.get('qtde')
    preco = data.get('preco')
    login_user = data.get('loginUser')
    
    if not nome or not qtde or not preco or not login_user:
        return jsonify({"error": "Todos os campos são obrigatórios!"}), 400
    
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('SELECT tipoUser FROM users WHERE loginUser = %s', (login_user,))
        user_type = cur.fetchone()
        
        if not user_type:
            return jsonify({"error": "Usuário não encontrado!"}), 404
        
        user_type = user_type[0]

        # Verifica se o usuário normal atingiu o limite de produtos
        if user_type == 'normal':
            cur.execute('SELECT COUNT(*) FROM produtos WHERE loginUser = %s', (login_user,))
            count = cur.fetchone()[0]
            if count >= 3:
                return jsonify({"error": "Você atingiu o limite de produtos!"}), 400

        # Insere o produto no banco de dados
        cur.execute('INSERT INTO produtos (nome, loginUser, qtde, preco) VALUES (%s, %s, %s, %s)', 
                    (nome, login_user, qtde, preco))
        conn.commit()

        return jsonify({"message": "Produto inserido com sucesso!"}), 201
    finally:
        cur.close()
        conn.close()


@app.route('/api/produto/<id_or_nome>', methods=['GET'])
def buscar_produto(id_or_nome):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Tenta buscar pelo ID primeiro
        if id_or_nome.isdigit():
            cur.execute('SELECT id, nome, qtde, preco FROM produtos WHERE id = %s', (id_or_nome,))
        else:
            cur.execute('SELECT id, nome, qtde, preco FROM produtos WHERE nome LIKE %s', (f"%{id_or_nome}%",))

        produto = cur.fetchone()
        
        if produto:
            return jsonify({
                "id": produto[0],
                "nome": produto[1],
                "qtde": produto[2],
                "preco": produto[3]
            }), 200
        else:
            return jsonify({"error": "Produto não encontrado!"}), 404
    finally:
        cur.close()
        conn.close()


@app.route('/api/produtos', methods=['GET'])
def listar_produtos_api():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT id, nome, qtde, preco FROM produtos;")
    produtos = cur.fetchall()
    
    cur.close()
    conn.close()

    #lista dicionarios
    produtos_list = [{
        "id": produto[0],
        "nome": produto[1],
        "qtde": produto[2],
        "preco": produto[3]
    } for produto in produtos]

    return jsonify(produtos_list), 200


@app.route('/api/usuarios', methods=['GET'])
def listar_usuarios():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT loginUser, tipoUser FROM users;")
    usuarios = cur.fetchall()
    
    cur.close()
    conn.close()

    # Cria uma lista de dicionários para retornar em JSON
    usuarios_list = [{
        "loginUser": usuario[0],
        "tipoUser": usuario[1]
    } for usuario in usuarios]

    return jsonify(usuarios_list), 200

@app.route('/grafico_vendas')
def grafico_vendas():
    conn = get_db_connection()
    
    try:
        cur = conn.cursor()
        
        cur.execute('''
            SELECT produto_id, quantidade, data
            FROM vendas
        ''')
        
        vendas = cur.fetchall()
        
        # Criando um Dataframe
        df = pd.DataFrame(vendas, columns=['produto_id', 'quantidade', 'data'])
        
        # Removo coluna data antes de realizar a soma
        df_agrupado = df[['produto_id', 'quantidade']].groupby('produto_id').sum().reset_index()
        
        # Crio o gráfico usando Plotly
        fig = px.bar(
            df_agrupado, 
            x='produto_id', 
            y='quantidade', 
            title="Total de Produtos Vendidos", 
            labels={'quantidade': 'Quantidade Vendida', 'produto_id': 'ID do Produto'}
        )
        
        graph_html = fig.to_html(full_html=False)
        
    finally:
        cur.close()
        conn.close()
    
    return render_template('grafico_vendas.html', graph_html=graph_html)



@app.route('/comprar/<int:produto_id>', methods=['POST'])
def comprar_produto(produto_id):
    if 'loginUser' not in session:  # Verifica se o usuário está logado
        return redirect(url_for('login'))

    quantidade = int(request.form['quantidade'])
    login_user = session['loginUser']

    conn = get_db_connection()
    try:
        cur = conn.cursor()

        cur.execute('SELECT qtde FROM produtos WHERE id = %s', (produto_id,))
        produto = cur.fetchone()

        if not produto:
            return "Produto não encontrado.", 404

        estoque_atual = produto[0]

        if quantidade > estoque_atual:
            return "Quantidade insuficiente no estoque.", 400

        # Atualizar estoque
        novo_estoque = estoque_atual - quantidade
        cur.execute('UPDATE produtos SET qtde = %s WHERE id = %s', (novo_estoque, produto_id))

        # Registrar venda
        cur.execute(
            'INSERT INTO vendas (produto_id, quantidade, preco, usuario_id, data) '
            'SELECT %s, %s, preco, id, NOW() FROM produtos WHERE id = %s',
            (produto_id, quantidade, produto_id)
        )

        conn.commit()
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('listar_produtos'))


if __name__ == '__main__':
    app.run(debug=True)
