

import streamlit as st
import sqlite3
import pandas as pd
import os  # Para acessar variáveis de ambiente

# Caminho do banco de dados
DB_DIR = "./streamlit"
DB_PATH = os.path.join(DB_DIR, "compras.db")

# Criar o diretório do banco de dados se não existir
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

# Conexão com o banco de dados SQLite
def create_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    return conn

# Criar a tabela se não existir
def create_table():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS lista_compras (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item TEXT NOT NULL,
        quantidade INTEGER NOT NULL,
        unidade TEXT NOT NULL,
        valor_unitario REAL NOT NULL DEFAULT 0.0,
        comprado BOOLEAN NOT NULL DEFAULT 0
    )
    ''')
    conn.commit()
    conn.close()

# Adicionar a coluna valor_unitario caso não exista
def add_column():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('PRAGMA table_info(lista_compras);')
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'valor_unitario' not in columns:
        cursor.execute('ALTER TABLE lista_compras ADD COLUMN valor_unitario REAL NOT NULL DEFAULT 0.0')
        conn.commit()
    
    conn.close()

# Adicionar item à lista
def add_item(item, quantidade, unidade, valor_unitario):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO lista_compras (item, quantidade, unidade, valor_unitario) VALUES (?, ?, ?, ?)', 
                   (item, quantidade, unidade, valor_unitario))
    conn.commit()
    conn.close()

# Obter todos os itens da lista
def get_items():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, item, quantidade, unidade, valor_unitario, comprado FROM lista_compras')
    items = cursor.fetchall()
    conn.close()
    return items

# Excluir item da lista
def delete_item(item_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM lista_compras WHERE id = ?', (item_id,))
    conn.commit()
    conn.close()

# Excluir todos os itens da lista com senha segura
def delete_all_items(password):
    system_password = st.secrets["DIRETIVA1"]  # Obtém a senha do arquivo secrets do Streamlit
    if password == system_password:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM lista_compras')
        conn.commit()
        conn.close()
        return True
    return False

# Marcar item como comprado
def mark_as_purchased(item_id, purchased):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE lista_compras SET comprado = ? WHERE id = ?', (purchased, item_id))
    conn.commit()
    conn.close()

# Inicializar a aplicação
create_table()
add_column()

st.title("Lista de Compras")

# Formulário para adicionar um item
item = st.text_input("Digite o item que deseja adicionar:")
quantidade = st.number_input("Digite a quantidade:", min_value=1)
unidade = st.selectbox("Selecione a unidade:", ["quilo", "litro", "unidade"])
valor_unitario = st.number_input("Digite o valor unitário:", min_value=0.01, format="%.2f")

if st.button("Adicionar"):
    if item and valor_unitario > 0:
        add_item(item, quantidade, unidade, valor_unitario)
        st.success(f"'{quantidade} {unidade} de {item} (R${valor_unitario:.2f})' adicionado à lista!")
    else:
        st.warning("Por favor, insira um item e um valor válido.")

# Exibir itens da lista
st.subheader("Itens na lista de compras:")
items = get_items()

if items:
    items_df = pd.DataFrame(items, columns=["ID", "Item", "Quantidade", "Unidade", "Valor Unitário", "Comprado"])
    items_df["Comprado"] = items_df["Comprado"].apply(lambda x: "✔" if x else "❌")

    # Calcular e exibir o valor total da compra
    items_df["Total"] = items_df["Quantidade"] * items_df["Valor Unitário"]
    valor_total = items_df["Total"].sum()

    st.table(items_df)
    st.subheader(f"Total da compra: R${valor_total:.2f}")

    # Opção para marcar item como comprado ou excluir um item
    item_to_update = st.number_input("Digite o ID do item a ser atualizado:", min_value=1, max_value=len(items))
    if st.button("Marcar como comprado"):
        mark_as_purchased(item_to_update, True)
        st.success(f"Item com ID {item_to_update} marcado como comprado!")
    if st.button("Excluir"):
        delete_item(item_to_update)
        st.success(f"Item com ID {item_to_update} excluído!")

    # Opção para excluir todos os itens com senha
    st.subheader("Excluir todos os itens")
    password_input = st.text_input("Digite a senha para excluir todos os itens:", type="password")
    if st.button("Confirmar exclusão"):
        if delete_all_items(password_input):
            st.success("Todos os itens foram excluídos!")
        else:
            st.error("Senha incorreta! Exclusão não permitida.")
else:
    st.info("A lista de compras está vazia.")