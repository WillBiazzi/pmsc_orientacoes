
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import json
import os
import hashlib
import unicodedata

app = Flask(__name__)
app.secret_key = 'segredo-top-seguro'

ARQUIVO_ORIENTACOES = 'orientacoes.json'
ARQUIVO_USUARIOS = 'usuarios.json'

# Funcoes auxiliares

def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def normalizar(texto):
    """Remove acentos e converte para minúsculo"""
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    ).lower()

def carregar_orientacoes():
    if os.path.exists(ARQUIVO_ORIENTACOES):
        with open(ARQUIVO_ORIENTACOES, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def salvar_orientacoes(lista):
    with open(ARQUIVO_ORIENTACOES, 'w', encoding='utf-8') as f:
        json.dump(lista, f, indent=4, ensure_ascii=False)

def carregar_usuarios():
    if os.path.exists(ARQUIVO_USUARIOS):
        with open(ARQUIVO_USUARIOS, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def salvar_usuarios(dados):
    with open(ARQUIVO_USUARIOS, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

# Carregamento inicial
db_orientacoes = carregar_orientacoes()
db_usuarios = carregar_usuarios()

@app.route('/')
def index():
    if not session.get('logado'):
        return redirect(url_for('login'))
    return render_template('index.html', tipo=session.get('tipo'))

@app.route('/buscar', methods=['POST'])
def buscar():
    data = request.get_json()
    termo = normalizar(data.get('termo', ''))
    resultados = []

    for o in db_orientacoes:
        texto = ' '.join([
            o.get('titulo', ''),
            o.get('categoria', ''),
            o.get('conteudo', ''),
            ' '.join(o.get('palavras_chave', []))
        ])
        if termo in normalizar(texto):
            resultados.append(o)

    return jsonify(resultados)

@app.route('/adicionar', methods=['POST'])
def adicionar():
    if session.get('tipo') != 'admin':
        return jsonify({"status": "erro", "mensagem": "Acesso não autorizado"}), 403

    data = request.get_json()
    nova = {
        "titulo": data.get('titulo', '').strip(),
        "categoria": data.get('categoria', '').strip(),
        "conteudo": data.get('conteudo', '').strip()
    }
    if nova['titulo'] and nova['categoria'] and nova['conteudo']:
        db_orientacoes.append(nova)
        salvar_orientacoes(db_orientacoes)
        return jsonify({"status": "ok"})
    else:
        return jsonify({"status": "erro", "mensagem": "Campos incompletos"}), 400

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        senha = request.form.get('senha')
        user = db_usuarios.get(usuario)

        if user and user['senha'] == hash_senha(senha):
            session['logado'] = True
            session['usuario'] = usuario
            session['tipo'] = user['tipo']
            return redirect(url_for('index'))
        else:
            return render_template('login.html', erro='Credenciais inválidas')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if not session.get('logado') or session.get('tipo') != 'admin':
        return redirect(url_for('login'))

    if request.method == 'POST':
        novo_usuario = request.form.get('usuario')
        senha = request.form.get('senha')
        tipo = request.form.get('tipo')

        if not novo_usuario or not senha or tipo not in ['admin', 'comum']:
            return render_template('cadastro.html', erro='Preencha todos os campos corretamente.')

        if novo_usuario in db_usuarios:
            return render_template('cadastro.html', erro='Usuário já existe.')

        db_usuarios[novo_usuario] = {
            "senha": hash_senha(senha),
            "tipo": tipo
        }
        salvar_usuarios(db_usuarios)
        return render_template('cadastro.html', sucesso='Usuário cadastrado com sucesso!')

    return render_template('cadastro.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
