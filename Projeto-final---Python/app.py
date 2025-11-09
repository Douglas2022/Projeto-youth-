from flask import Flask, render_template, request, redirect, url_for, session
import mysql
import mysql.connector as my

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'  # Necessário para sessões


def ConectarBanco():
    return my.connect(
        user='root',
        password='12345',
        database='SuperSelectD',
        host='localhost'
    )


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
            sql = "INSERT INTO usuarios (nome, email, senha, cpf, tipo) VALUES (%s,%s, %s, %s, %s)"
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

@app.route('/cliente')
def cliente():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))  # Redireciona se não estiver logado

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


@app.route('/produtos')
def produtos():
    try:
        conexao = ConectarBanco()
        cursor = conexao.cursor(dictionary=True)
        cursor.execute("SELECT * FROM produtos")
        lista_produtos = cursor.fetchall()
        cursor.close()
        conexao.close()
    except my.Error as err:
        lista_produtos = []
        print(f"Erro ao buscar produtos: {err}")
    
    return render_template('produtos.html', produtos=lista_produtos)

   

@app.route('/comentarios')
def comentarios():
    mensagem = None
  
    conexao = ConectarBanco()
    cursor = conexao.cursor(dictionary=True)
   
    if request.method == 'POST':
        nome = session.get('usuario_nome', 'Anônimo')
        texto = request.form.get('comentario')

        if texto.strip():
            try:
                sql = "INSERT INTO comentarios (nome, texto) VALUES (%s, %s)"
                cursor.execute(sql, (nome, texto))
                conexao.commit()
                mensagem = "Comentário enviado com sucesso!"
            except my.Error as err:
                mensagem = f"Erro ao salvar comentário: {err}"

    cursor.execute("SELECT * FROM comentarios ORDER BY id DESC")
    lista_comentarios = cursor.fetchall()

    cursor.close()
    conexao.close()

    return render_template('comentarios.html', comentarios=lista_comentarios, mensagem=mensagem)


@app.route('/cadastraProdutos', methods=['GET', 'POST'])
def cadastraProdutos():
    conexao = ConectarBanco()
    cursor = conexao.cursor(dictionary=True)
    mensagem = None

    if request.method == 'POST':
        nome = request.form['nome']
        marca = request.form['marca']
        tipo = request.form['tipo']
        preco = request.form['preco']
        link = request.form['link']

        # Inserir o produto no banco
        cursor.execute(
            "INSERT INTO produtos (nome, marca, tipo, preco, link) VALUES (%s, %s, %s, %s, %s)",
            (nome, marca, tipo, preco, link)
        )
        conexao.commit()
        mensagem = ' Produto cadastrado com sucesso!'

    # Buscar todos os produtos para exibir na tela
    cursor.execute("SELECT * FROM produtos")
    produtos = cursor.fetchall()

    cursor.close()
    conexao.close()

    return render_template('cadastraProdutos.html', mensagem=mensagem, produtos=produtos)



   


 

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



@app.route('/excluir_produto/<int:id>', methods=['POST'])
def excluir_produto(id):
    try:
        conexao = mysql.connector.connect(
           user='root',
            password='12345',
            database='SuperSelectD',
            host='localhost'
        )
        cursor = conexao.cursor()
        cursor.execute("DELETE FROM produtos WHERE id = %s", (id,))
        conexao.commit()
        cursor.close()
        conexao.close()
        return redirect(url_for('cadastraProdutos'))
    except Exception as e:
        return f"Erro ao excluir produto: {e}"




@app.route('/logout')
def logout():
    session.clear()  # Limpa todos os dados do usuário da sessão
    return redirect(url_for('login'))  # Redireciona para a página de login


if __name__ == '__main__':
    app.run(debug=True)
