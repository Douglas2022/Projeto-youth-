from flask import Flask, render_template, request, redirect, url_for, session, flash
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

    # Buscar produtos e comentários
    cursor.execute("SELECT * FROM produtos")
    produtos = cursor.fetchall()

    cursor.execute("SELECT * FROM comentarios ORDER BY id DESC")
    comentarios = cursor.fetchall()

    cursor.close()
    conexao.close()

    return render_template('cadastraProdutos.html',
                           mensagem=mensagem,
                           produtos=produtos,
                           comentarios=comentarios,
                           usuario_tipo=session.get('usuario_tipo'))


@app.route('/excluir_produto/<int:id>', methods=['POST'])
def excluir_produto(id):
    # Verifica se o usuário está logado e é administrador
    if 'usuario_id' not in session or session.get('usuario_tipo') != 'administrador':
        flash("Acesso negado.", "erro")
        return redirect(url_for('login'))

    try:
        conexao = ConectarBanco()
        cursor = conexao.cursor()

        # Exclui o produto com o ID recebido
        cursor.execute("DELETE FROM produtos WHERE id = %s", (id,))
        conexao.commit()

        flash("Produto excluído com sucesso!", "sucesso")
    except my.Error as e:
        flash(f"Erro ao excluir produto: {e}", "erro")
    finally:
        cursor.close()
        conexao.close()

    return redirect(url_for('cadastraProdutos'))

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



# ---------------- MIDDLEWARE ---------------- #

@app.before_request
def proteger_rotas_admin():
    admin_routes = ['cadastraProdutos', 'excluir_produto']
    if request.endpoint in admin_routes and session.get('usuario_tipo') != 'administrador':
        return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
