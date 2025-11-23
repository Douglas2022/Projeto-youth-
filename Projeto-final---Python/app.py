from flask import Flask, Response, render_template, request, redirect, url_for, session, flash
import mysql.connector as my
import os
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = '12345'

# Configuração de upload
UPLOAD_FOLDER = 'static/img'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ---------------- FUNÇÕES AUXILIARES ---------------- #
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
def ConectarBanco():
    return my.connect(
        host="localhost",
        user="root",
        password="12345",
        database="superselectd",  # nome correto em minúsculas
        charset="utf8mb4"
    )




# ---------------- ROTAS PÚBLICAS ---------------- #
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/administrador')
def administrador():
    return render_template('administrador.html')


@app.route('/cliente')
def cliente():
    try:
        conexao = ConectarBanco()
        cursor = conexao.cursor(dictionary=True)

        # Debug: qual banco está conectado
        cursor.execute("SELECT DATABASE()")
        db = cursor.fetchone()
        print("Banco conectado:", db)

        # Debug: quais tabelas existem
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print("Tabelas:", tables)

        # Buscar produtos
        cursor.execute("SELECT * FROM produtos")
        produtos = cursor.fetchall()
        print("Produtos:", produtos)

        # Buscar comentários
        cursor.execute("SELECT * FROM comentarios")
        comentarios = cursor.fetchall()
        print("Comentários:", comentarios)

        # Fechar cursor e conexão
        cursor.close()
        conexao.close()

        return render_template('cliente.html', produtos=produtos, comentarios=comentarios)

    except my.Error as err:
        return render_template('cliente.html', produtos=[], comentarios=[], mensagem=f"Erro ao carregar dados: {err}")

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    mensagem = None
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip()
        cpf = request.form.get('cpf', '').strip()
        senha = request.form.get('senha', '').strip()

        if not all([nome, email, cpf, senha]):
            mensagem = "Preencha todos os campos!"
            return render_template('cadastro.html', mensagem=mensagem)

        cpf_limpo = cpf.replace('.', '').replace('-', '')

        try:
            conexao = ConectarBanco()
            cursor = conexao.cursor(dictionary=True)

            cursor.execute("SELECT * FROM usuarios WHERE email=%s", (email,))
            if cursor.fetchone():
                mensagem = "Este email já está cadastrado!"
            else:
                cursor.execute("SELECT * FROM usuarios WHERE cpf=%s", (cpf_limpo,))
                if cursor.fetchone():
                    mensagem = "Este CPF já está cadastrado!"
                else:
                    # Salva senha em texto puro
                    cursor.execute(
                        "INSERT INTO usuarios (nome, email, senha, cpf, tipo) VALUES (%s,%s,%s,%s,%s)",
                        (nome, email, senha, cpf_limpo, 'cliente')
                    )
                    conexao.commit()
                    flash("Cadastro realizado com sucesso!", "sucesso")
                    return redirect(url_for('login'))

            cursor.close()
            conexao.close()

        except my.Error as err:
            mensagem = f"Erro ao cadastrar: {err}"

    return render_template('cadastro.html', mensagem=mensagem)

@app.route('/login', methods=['GET', 'POST'])
def login():
    mensagem = None
    if request.method == 'POST':
        login_input = request.form.get('login', '').strip()
        senha_digitada = request.form.get('senha', '').strip()

        try:
            conexao = ConectarBanco()
            cursor = conexao.cursor(dictionary=True)

            if login_input.replace('.', '').replace('-', '').isdigit():
                cpf = login_input.replace('.', '').replace('-', '')
                cursor.execute("SELECT * FROM usuarios WHERE cpf=%s", (cpf,))
            else:
                cursor.execute("SELECT * FROM usuarios WHERE email=%s", (login_input,))

            usuario = cursor.fetchone()
            cursor.close()
            conexao.close()

            if usuario:
                senha_banco = usuario['senha'].strip()

                # Comparação direta sem hash
                if senha_banco == senha_digitada:
                    session['usuario_id'] = usuario['id']
                    session['usuario_nome'] = usuario['nome']
                    session['usuario_tipo'] = usuario['tipo'].strip().lower()

                    if session['usuario_tipo'] == 'administrador':
                        return redirect(url_for('cadastraProdutos'))
                    else:
                        return redirect(url_for('cliente'))
                else:
                    mensagem = "CPF/Email ou senha incorretos."
            else:
                mensagem = "Usuário não encontrado."

        except my.Error as err:
            mensagem = f"Erro ao logar: {err}"

    return render_template('login.html', mensagem=mensagem)

@app.route('/cadastraProdutos', methods=['GET', 'POST'])
def cadastraProdutos():
    if 'usuario_id' not in session or session.get('usuario_tipo') != 'administrador':
        flash("Acesso negado.", "erro")
        return redirect(url_for('login'))

    try:
        conexao = ConectarBanco()
        cursor = conexao.cursor(dictionary=True)

        # --------------------
        #     SE FOR POST
        # --------------------
        if request.method == 'POST':
            nome = request.form.get('nome')
            marca = request.form.get('marca')
            tipo = request.form.get('tipo')
            preco = request.form.get('preco')
            quantidade = request.form.get('quantidade')
            link = request.form.get('link')

            sql = """
                INSERT INTO produtos (nome, marca, tipo, preco, quantidade, link)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (nome, marca, tipo, preco, quantidade, link))
            conexao.commit()

            flash("Produto cadastrado com sucesso!", "sucesso")

            # Redireciona para a mesma página para evitar reenvio de formulário
            return redirect(url_for('cadastraProdutos'))

        # --------------------
        #     SE FOR GET
        # --------------------
        cursor.execute("SELECT * FROM produtos")
        produtos = cursor.fetchall()

        cursor.close()
        conexao.close()

        return render_template(
            'cadastraProdutos.html',
            produtos=produtos,
            usuario_tipo=session.get('usuario_tipo')
        )

    except my.Error as err:
        return render_template(
            'cadastraProdutos.html', 
            produtos=[], 
            mensagem=f"Erro: {err}",
            usuario_tipo=session.get('usuario_tipo')
        )

    
@app.route('/comentar/<int:produto_id>', methods=['GET', 'POST'])
def comentar(produto_id):
    if 'usuario_id' not in session:
        flash("Faça login para comentar.", "erro")
        return redirect(url_for('home'))

    conexao = ConectarBanco()
    cursor = conexao.cursor(dictionary=True)

    # Buscar dados do produto
    cursor.execute("SELECT * FROM produtos WHERE id = %s", (produto_id,))
    produto = cursor.fetchone()

    if not produto:
        cursor.close()
        conexao.close()
        flash("Produto não encontrado.", "erro")
        return redirect(url_for('home'))

    # Se enviou o formulário
    if request.method == "POST":
        texto = request.form.get("texto")
        nome_usuario = session.get("usuario_nome")

        if texto:
            cursor.execute("""
                INSERT INTO comentarios (produto_id, nome_usuario, texto)
                VALUES (%s, %s, %s)
            """, (produto_id, nome_usuario, texto))
            conexao.commit()

            flash("Comentário enviado!", "sucesso")

            cursor.close()
            conexao.close()
            return redirect(url_for('home'))

    # Se for GET → mostra a página de comentário
    cursor.execute("SELECT * FROM comentarios WHERE produto_id = %s", (produto_id,))
    comentarios = cursor.fetchall()

    cursor.close()
    conexao.close()

    return render_template("comentar.html", produto=produto, comentarios=comentarios)

@app.route('/excluir_produto/<int:id>', methods=['POST'])
def excluir_produto(id):
    if 'usuario_id' not in session or session.get('usuario_tipo') != 'administrador':
        flash("Acesso negado.", "erro")
        return redirect(url_for('login'))

    try:
        conexao = ConectarBanco()
        cursor = conexao.cursor()
        cursor.execute("DELETE FROM produtos WHERE id=%s", (id,))
        conexao.commit()
        cursor.close()
        conexao.close()
        flash("Produto excluído com sucesso!", "sucesso")
    except my.Error as e:
        flash(f"Erro ao excluir produto: {e}", "erro")

    return redirect(url_for('cadastraProdutos'))

@app.before_request
def proteger_rotas_admin():
    admin_routes = ['cadastraProdutos', 'excluir_produto']
    if request.endpoint in admin_routes and session.get('usuario_tipo') != 'administrador':
        return redirect(url_for('login'))
    
@app.route('/imagem/<int:produto_id>')
def mostrar_imagem(produto_id):
    conexao = ConectarBanco()
    cursor = conexao.cursor(dictionary=True)
    cursor.execute("SELECT link FROM produtos WHERE id=%s", (produto_id,))
    produto = cursor.fetchone()
    cursor.close()
    conexao.close()

    if produto and produto['link']:
        # Se for um arquivo local
        if not produto['link'].startswith("http"):
            caminho = os.path.join(app.config['UPLOAD_FOLDER'], produto['link'])
            with open(caminho, 'rb') as f:
                return Response(f.read(), mimetype='image/jpeg')
        else:
            # Se for link da web, basta usar direto no template
            return redirect(produto['link'])
    return "Imagem não encontrada", 404


@app.route('/logout')
def logout():
    session.clear()
    flash("Você saiu da conta.", "sucesso")
    return redirect(url_for('index'))

@app.route('/produtos_json')
def produtos_json():
    conexao = ConectarBanco()
    cursor = conexao.cursor(dictionary=True)
    cursor.execute("SELECT * FROM produtos")
    produtos = cursor.fetchall()
    cursor.close()
    conexao.close()
    return {"produtos": produtos}

@app.route('/relatorios')
def relatorios():
    return render_template('relatorios.html')



if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(host='127.0.0.1', port=5000, debug=True)
