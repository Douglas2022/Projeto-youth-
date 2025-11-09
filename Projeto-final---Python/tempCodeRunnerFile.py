@app.route('/Loja', methods=['GET', 'POST'])
def Loja():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    mensagem = None
    usuario_nome = session.get('usuario_nome', 'Anônimo')

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

    return render_template('Loja.html', produtos=produtos, comentarios=comentarios, mensagem=mensagem, nome=usuario_nome)
