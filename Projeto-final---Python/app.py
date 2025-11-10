from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector as my

app = Flask(__name__)
app.secret_key = '12345'


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

from flask import Flask, render_template, request, redirect, url_for, session, flash

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
            # Aqui você renderiza novamente o login com a mensagem de erro
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

    return render_template('cliente.html', produtos=produtos, comentarios=comentarios, mensagem=mensagem, nome=usuario_nome)

@app.route('/historico')
def historico():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    try:
        conexao = ConectarBanco()
        cursor = conexao.cursor(dictionary=True)

        sql = """
            SELECT h.id, p.nome AS produto, p.marca, p.preco, h.data_compra
            FROM historico_compras h
            JOIN produtos p ON h.produto_id = p.id
            WHERE h.usuario_id = %s
            ORDER BY h.data_compra DESC
        """
        cursor.execute(sql, (session['usuario_id'],))
        historico_usuario = cursor.fetchall()

        cursor.close()
        conexao.close()
    except my.Error as err:
        historico_usuario = []
        print(f"Erro ao buscar histórico: {err}")

    return render_template('historico.html', historico=historico_usuario, nome=session['usuario_nome'])

from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector as my

from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector as my


@app.route('/Loja', methods=['GET', 'POST'])
def Loja():
    usuario_nome = session.get('usuario_nome', None)

    # 🔒 Se o usuário não estiver logado:
    if 'usuario_id' not in session:
        if request.method == 'POST':
            cpf_digitado = request.form.get('cpf', '').replace('.', '').replace('-', '')
            senha = request.form.get('senha', '')

            conexao = ConectarBanco()
            cursor = conexao.cursor(dictionary=True)
            cursor.execute('SELECT * FROM usuarios')
            usuarios = cursor.fetchall()
            cursor.close()
            conexao.close()

            # Verifica login
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
                flash(f"Bem-vindo, {usuario['nome']}!", "sucesso")
                return redirect(url_for('Loja'))
            else:
                flash("CPF ou senha incorretos.", "erro")

        # Exibe tela de login se não estiver logado
        return render_template('Loja.html', logado=False)

    # ✅ Se o usuário estiver logado, mostra produtos em cards
    try:
        conexao = ConectarBanco()
        cursor = conexao.cursor(dictionary=True)
        cursor.execute("SELECT * FROM produtos")
        produtos = cursor.fetchall()
        cursor.close()
        conexao.close()

        return render_template(
            'Loja.html',
            logado=True,
            usuario_nome=usuario_nome,
            produtos=produtos
        )

    except Exception as e:
        print("Erro ao carregar produtos:", e)
        flash("Erro ao carregar produtos.", "erro")
        return render_template('Loja.html', logado=True, produtos=[], usuario_nome=usuario_nome)

# ---------------- ROTAS ADMIN ---------------- #

@app.route('/cadastraProdutos', methods=['GET', 'POST'])
def cadastraProdutos():
    if 'usuario_id' not in session or session.get('usuario_tipo') != 'administrador':
        return redirect(url_for('login'))

    conexao = ConectarBanco()
    cursor = conexao.cursor(dictionary=True)
    mensagem = None

    if request.method == 'POST':
        nome = request.form['nome']
        marca = request.form['marca']
        tipo = request.form['tipo']
        preco = request.form['preco']
        link = request.form['link']
        try:
            cursor.execute(
                "INSERT INTO produtos (nome, marca, tipo, preco, link) VALUES (%s, %s, %s, %s, %s)",
                (nome, marca, tipo, preco, link)
            )
            conexao.commit()
            mensagem = "Produto cadastrado com sucesso!"
        except my.Error as err:
            mensagem = f"Erro ao cadastrar produto: {err}"

    cursor.execute("SELECT * FROM produtos")
    produtos = cursor.fetchall()
    cursor.close()
    conexao.close()

    return render_template('cadastraProdutos.html', mensagem=mensagem, produtos=produtos)

@app.route('/excluir_produto/<int:id>', methods=['POST'])
def excluir_produto(id):
    if 'usuario_id' not in session or session.get('usuario_tipo') != 'administrador':
        return redirect(url_for('login'))

    try:
        conexao = ConectarBanco()
        cursor = conexao.cursor()
        cursor.execute("DELETE FROM produtos WHERE id = %s", (id,))
        conexao.commit()
        cursor.close()
        conexao.close()
        return redirect(url_for('cadastraProdutos'))
    except my.Error as e:
        return f"Erro ao excluir produto: {e}"

# ---------------- MIDDLEWARE ---------------- #

@app.before_request
def proteger_rotas_admin():
    admin_routes = ['cadastraProdutos', 'excluir_produto']
    if request.endpoint in admin_routes and session.get('usuario_tipo') != 'administrador':
        return redirect(url_for('login'))

# ---------------- RODA O FLASK ---------------- #

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
