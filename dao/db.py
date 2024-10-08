import psycopg2
from psycopg2 import sql

#Estabelecendo a conexao com o bd.
def get_db_connection():
    conn = psycopg2.connect(
        host="dpg-crl0hgaj1k6c738lo0lg-a.oregon-postgres.render.com",
        database="sistema_gerenciamento_3x39",
        user="sistema_gerenciamento_3x39_user",
        password="gwqbHAuqt1R8NsRWXoiP5QPjbdEQhvKV"
    )
    return conn


def create_tables():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        loginUser VARCHAR(50) PRIMARY KEY,
        senha VARCHAR(100) NOT NULL,
        tipoUser VARCHAR(10) NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS produtos (
        id SERIAL PRIMARY KEY,
        nome VARCHAR(100),
        loginUser VARCHAR(50) REFERENCES users(loginUser),
        qtde INT,
        preco DECIMAL(10, 2)
    );
    """)

    conn.commit() #alteração no bd.
    cur.close()
    conn.close()


create_tables()