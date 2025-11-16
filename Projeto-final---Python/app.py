from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector as my
import os
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = '12345'

# Configuração de upload de imagens
UPLOAD_FOLDER = 'static/img'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def ConectarBanco():
    return my.connect(
        user='root',
        password='12345',
        database='SuperSelectD',
        host='localhost'
    )

# ---------------- ROTAS PÚBLICAS ---------------- #
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    mensagem = None
    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        cpf = request.form.get('cpf')
        senha = request.form.get('senha')
        try:
            conexao = ConectarBanco()
            cursor = conexao.cursor()
            sql = "INSERT INTO usuarios (nome, email, senha, cpf, tipo) VALUES (%s,%s,%s,%s,%s)"
            cursor.execute(sql, (nome, email, senha, cpf, 'cliente'))
            conexao.commit()
            cursor.close()
            conexao.close()
            return redirect(url_for('login'))
        except my.Error as err:
            mensagem = f"Erro ao cadastrar: {err}"
    return render_template('cadastro.html', mensagem=mensagem)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        cpf_digitado = request.form.get('cpf').replace('.', '').replace('-', '')
        senha = request.form.get('senha')
        conexao = ConectarBanco()
        cursor = conexao.cursor(dictionary=True)
        cursor.execute('SELECT * FROM usuarios')
        usuarios = cursor.fetchall()
        cursor.close()
        conexao.close()

        usuario = None
        for u in usuarios:
            cpf_banco = u['cpf'].replace('.', '').replace('-', '')
            if cpf_banco == cpf_digitado and u['senha'] == senha:
                usuario = u
                break

        if usuario:
            session['usuario_id'] = usuario['id']
            session['usuario_nome'] = usuario['nome']
            session['usuario_tipo'] = usuario['tipo'].strip().lower()

            if session['usuario_tipo'] == 'administrador':
                return redirect(url_for('cadastraProdutos'))
            else:
                return redirect(url_for('cliente'))
        else:
            return render_template('login.html', mensagem="CPF ou senha incorreta.")
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ---------------- ROTAS CLIENTE ---------------- #
@app.route('/cliente', methods=['GET', 'POST'])
def cliente():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    mensagem = None
    usuario_nome = session['usuario_nome']
    usuario_tipo = session.get('usuario_tipo')

    try:
        conexao = ConectarBanco()
        cursor = conexao.cursor(dictionary=True)

        if request.method == 'POST':
            produto_id = request.form.get('produto_id')
            texto = request.form.get('texto')
            if texto.strip():
                sql_insert = "INSERT INTO comentarios (produto_id, nome_usuario, texto) VALUES (%s, %s, %s)"
                cursor.execute(sql_insert, (produto_id, usuario_nome, texto))
                conexao.commit()
                mensagem = "Comentário enviado com sucesso!"

        cursor.execute("SELECT * FROM produtos")
        produtos = cursor.fetchall()

        cursor.execute("SELECT * FROM comentarios ORDER BY id DESC")
        comentarios = cursor.fetchall()

        cursor.close()
        conexao.close()
    except my.Error as err:
        produtos = []
        comentarios = []
        mensagem = f"Erro ao acessar dados: {err}"

    return render_template(
        'cliente.html',
        produtos=produtos,
        comentarios=comentarios,
        mensagem=mensagem,
        usuario_nome=usuario_nome,
        usuario_tipo=usuario_tipo,
        logado=True
    )

# ---------------- ROTAS ADMIN ---------------- #
@app.route('/cadastraProdutos', methods=['GET', 'POST'])
def cadastraProdutos():
    if 'usuario_id' not in session or session.get('usuario_tipo') != 'administrador':
        return redirect(url_for('login'))

    mensagem = None
    conexao = ConectarBanco()
    cursor = conexao.cursor(dictionary=True)

    if request.method == 'POST':
        nome = request.form['nome']
        marca = request.form['marca']
        tipo = request.form['tipo']
        preco = request.form['preco']
        quantidade = request.form['quantidade']

        # Upload de imagem
        arquivo = request.files.get('imagem')
        link = None
        if arquivo and allowed_file(arquivo.filename):
            filename = secure_filename(arquivo.filename)
            arquivo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            link = f"img/{filename}"  # caminho relativo para usar no template
            print("Imagem salva:", link)  # DEBUG

        try:
            cursor.execute(
                "INSERT INTO produtos (nome, marca, tipo, preco, quantidade, link) VALUES (%s, %s, %s, %s, %s, %s)",
                (nome, marca, tipo, preco, quantidade, link)
            )
            conexao.commit()
            mensagem = "Produto cadastrado com sucesso!"
        except my.Error as err:
            mensagem = f"Erro ao cadastrar produto: {err}"

    # Buscar todos produtos
    cursor.execute("SELECT * FROM produtos")
    produtos = cursor.fetchall()
    cursor.close()
    conexao.close()

    return render_template('cadastraProdutos.html',
                           mensagem=mensagem,
                           produtos=produtos)

# ---------------- COMENTÁRIOS ---------------- #
@app.route('/comentar/<int:produto_id>', methods=['POST'])
def comentar_produto(produto_id):
    nome_usuario = request.form.get('nome_usuario')
    texto = request.form.get('texto')

    try:
        conexao = ConectarBanco()
        cursor = conexao.cursor()
        cursor.execute("INSERT INTO comentarios (produto_id, nome_usuario, texto) VALUES (%s, %s, %s)",
                       (produto_id, nome_usuario, texto))
        conexao.commit()
        cursor.close()
        conexao.close()
        flash("Comentário adicionado!", "sucesso")
    except Exception as e:
        print("Erro ao adicionar comentário:", e)
        flash("Erro ao adicionar comentário.", "erro")

    return redirect(url_for('cliente'))

@app.route('/excluir_comentario/<int:comentario_id>', methods=['POST'])
def excluir_comentario(comentario_id):
    if 'usuario_id' not in session or session.get('usuario_tipo') != 'administrador':
        flash("Acesso negado.", "erro")
        return redirect(url_for('login'))

    try:
        conexao = ConectarBanco()
        cursor = conexao.cursor()
        cursor.execute("DELETE FROM comentarios WHERE id = %s", (comentario_id,))
        conexao.commit()
        cursor.close()
        conexao.close()
        flash("Comentário excluído com sucesso!", "sucesso")
    except my.Error as e:
        flash(f"Erro ao excluir comentário: {e}", "erro")

    return redirect(url_for('cadastraProdutos'))

# ---------------- RELATÓRIOS ---------------- #
@app.route('/relatorios')
def relatorios():
    if 'usuario_id' not in session or session.get('usuario_tipo') != 'administrador':
        return redirect(url_for('login'))

    conexao = ConectarBanco()
    cursor = conexao.cursor(dictionary=True)

    cursor.execute("SELECT * FROM produtos")
    produtos = cursor.fetchall()

    cursor.execute("SELECT * FROM comentarios ORDER BY id DESC")
    comentarios = cursor.fetchall()

    alertas = []
    hoje = datetime.now().date()

    for p in produtos:
        if p['quantidade'] is not None and p['quantidade'] < 5:
            alertas.append({
                "produto": p['nome'],
                "tipo": "Estoque baixo",
                "mensagem": f"Apenas {p['quantidade']} unidades restantes."
            })

        if 'validade' in p and p['validade'] is not None:
            validade = p['validade']
            dias = (validade - hoje).days
            if dias <= 10:
                alertas.append({
                    "produto": p['nome'],
                    "tipo": "Validade próxima",
                    "mensagem": f"O produto vence em {dias} dias ({validade})."
                })

    cursor.close()
    conexao.close()

    return render_template('relatorios.html',
                           produtos=produtos,
                           comentarios=comentarios,
                           alertas=alertas)

# ---------------- EXCLUIR PRODUTO ---------------- #
@app.route('/excluir_produto/<int:id>', methods=['POST'])
def excluir_produto(id):
    if 'usuario_id' not in session or session.get('usuario_tipo') != 'administrador':
        flash("Acesso negado.", "erro")
        return redirect(url_for('login'))

    try:
        conexao = ConectarBanco()
        cursor = conexao.cursor()
        cursor.execute("DELETE FROM produtos WHERE id = %s", (id,))
        conexao.commit()
        cursor.close()
        conexao.close()
        flash("Produto excluído com sucesso!", "sucesso")
    except my.Error as e:
        flash(f"Erro ao excluir produto: {e}", "erro")

    return redirect(url_for('cadastraProdutos'))

# ---------------- MIDDLEWARE ---------------- #
@app.before_request
def proteger_rotas_admin():
    admin_routes = ['cadastraProdutos', 'excluir_produto']
    if request.endpoint in admin_routes and session.get('usuario_tipo') != 'administrador':
        return redirect(url_for('login'))

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(host='127.0.0.1', port=5000, debug=True)
