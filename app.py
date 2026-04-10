from flask import Flask, render_template, request, jsonify, session, redirect
import sqlite3
import os
from openai import OpenAI
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev_key")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
if not os.getenv("OPENAI_API_KEY"):
    print("⚠️ API KEY não configurada")

# conexão
def conectar():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

# criar banco
def criar_banco():
    conn = conectar()
    cursor = conn.cursor()

    # alertas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alertas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        localizacao TEXT,
        mensagem TEXT
    )
    """)

    # usuarios
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        email TEXT UNIQUE,
        senha TEXT,
        telefone TEXT,
        tipo TEXT
    )
    """)

    conn.commit()
    conn.close()

# criar admin
def criar_admin():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM usuarios WHERE email=?", ("admin@sos.com",))
    user = cursor.fetchone()

    if not user:
        senha_hash = generate_password_hash("1234")

        cursor.execute("""
        INSERT INTO usuarios (nome, email, senha, telefone, tipo)
        VALUES (?, ?, ?, ?, ?)
        """, ("Admin", "admin@sos.com", senha_hash, "000000000", "admin"))

    conn.commit()
    conn.close()

# 👉 CHAMAR AQUI (ANTES DAS ROTAS)
criar_banco()
criar_admin()



# ================= ROTAS =================

@app.route("/")
def index():
    return render_template("login.html")


# rota do registro

@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        nome = request.form["nome"]
        email = request.form["email"]
        senha = request.form["senha"]
        telefone = request.form["telefone"]

        # validação
        if not nome or not email or not senha:
            return render_template("registro.html", erro="Preencha todos os campos")

        conn = conectar()
        cursor = conn.cursor()

        # verifica se já existe
        cursor.execute("SELECT * FROM usuarios WHERE email=?", (email,))
        usuario = cursor.fetchone()

        if usuario:
            conn.close()
            return render_template("registro.html", erro="Email já cadastrado")

        # hash da senha
        senha_hash = generate_password_hash(senha)

        # salvar
        cursor.execute("""
        INSERT INTO usuarios (nome, email, senha, telefone, tipo)
        VALUES (?, ?, ?, ?, ?)
        """, (nome, email, senha_hash, telefone, "user"))

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("registro.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        senha = request.form["senha"]

        conn = conectar()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM usuarios WHERE email=?",
            (email,)
        )

        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user["senha"], senha):
            session["user_id"] = user["id"]
            session["tipo"] = user["tipo"]

            if user["tipo"] == "admin":
                return redirect("/dashboard")
            else:
                return redirect("/sos")

        return render_template("login.html", erro="Email ou senha inválidos")
    
    return render_template("login.html")


@app.route("/sos")
def sos():
    if "user_id" not in session:
        return redirect("/login")

    return render_template("sos.html")

@app.route("/ajuda")
def ajuda():
    return render_template("ajuda.html")

@app.route("/dashboard")
def dashboard():
    if "tipo" not in session or session["tipo"] != "admin":
        return redirect("/login")

    return render_template("dashboard.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# salvar alerta
@app.route("/alerta", methods=["POST"])
def alerta():
    data = request.get_json()

    if not data or "localizacao" not in data or "mensagem" not in data:
        return jsonify({"erro": "dados inválidos"}), 400

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO alertas (localizacao, mensagem) VALUES (?, ?)",
        (data["localizacao"], data["mensagem"])
    )

    conn.commit()
    conn.close()

    return jsonify({"status": "ok"})

# listar alertas
@app.route("/alertas", methods=["GET"])
def listar_alertas():
    if "tipo" not in session or session["tipo"] != "admin":
        return jsonify({"erro": "acesso negado"}), 403

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM alertas")
    dados = cursor.fetchall()

    conn.close()

    return jsonify([
        {"id": d["id"], "localizacao": d["localizacao"], "mensagem": d["mensagem"]}
        for d in dados
    ])

# upload áudio


@app.route("/upload_audio", methods=["POST"])
def upload_audio():
    if "audio" not in request.files:
        return {"erro": "nenhum arquivo enviado"}, 400

    audio = request.files["audio"]

    nome_arquivo = f"{uuid.uuid4()}.webm"
    audio.save(nome_arquivo)

    try:
        with open(nome_arquivo, "rb") as f:
            transcricao = client.audio.transcriptions.create(
            model="gpt-4o-mini-transcribe",
            file=f
        )
    finally:
        os.remove(nome_arquivo)

    return {"texto": transcricao.text}

# denuncia
@app.route('/denuncia', methods=['POST'])
def denuncia():
    data = request.get_json()

    if not data or "descricao" not in data:
        return jsonify({"erro": "dados inválidos"}), 400

    descricao = data["descricao"]

    print("DENÚNCIA:", descricao)

    return jsonify({"status": "ok"})

# usuário já logado não precisa fazer login  dnv


# rodar app
if __name__ == "__main__":
    app.run(debug=True)
