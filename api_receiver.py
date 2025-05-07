from fastapi import FastAPI, Request
import sqlite3

app = FastAPI()

# Criando a tabela no banco se não existir
def criar_tabela():
    conn = sqlite3.connect("dados_formulario.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS formulario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            cpf TEXT,
            rg TEXT,
            sexo TEXT,
            data_nascimento TEXT,
            idade INTEGER,
            cidade TEXT,
            estado TEXT,
            endereco TEXT,
            latitude TEXT,
            longitude TEXT
        )
    ''')
    conn.commit()
    conn.close()

criar_tabela()

@app.post("/webhook")
async def receber_dados(request: Request):
    try:
        dados = await request.json()  # Recebe os dados enviados pelo Formidable Forms

        nome = dados.get("nome", "Não informado")
        cpf = dados.get("cpf", "Não informado")
        rg = dados.get("rg", "Não informado")
        sexo = dados.get("sexo", "Não informado")
        data_nascimento = dados.get("data_nascimento", "Não informado")
        idade = dados.get("idade", 0)
        cidade = dados.get("cidade", "Não informado")
        estado = dados.get("estado", "Não informado")
        endereco = dados.get("endereco_completo", "Não informado")
        latitude = dados.get("latitude", "0.0")
        longitude = dados.get("longitude", "0.0")

        # Inserindo os dados no banco SQLite
        conn = sqlite3.connect("dados_formulario.db")
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO formulario (nome, cpf, rg, sexo, data_nascimento, idade, cidade, estado, endereco, latitude, longitude)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (nome, cpf, rg, sexo, data_nascimento, idade, cidade, estado, endereco, latitude, longitude))
        conn.commit()
        conn.close()

        return {"status": "ok", "mensagem": "Dados recebidos e armazenados com sucesso"}

    except Exception as e:
        return {"status": "erro", "mensagem": str(e)}
