import os 
from metodos_conexao import *
from flask import Flask, request, jsonify
import bcrypt 

#-----------------------------
#    CONEXÃO COM O SGBD
#-----------------------------

conexao = criarConexao(
    os.getenv("DB_HOST"),
    os.getenv("DB_USER"),
    os.getenv("DB_PASSWORD"),
    os.getenv("DB_NAME")
)


#-----------------------------
#    VALIDAÇÃO DO CPF
#-----------------------------

def validarCPF():
    dados = request.json()
    cpf = dados.get('cpf')
    if not cpf:
        return jsonify({'status': 'error', 'mensagem': 'CPF não enviado'}), 400

    cpf = cpf.replace('.', '').replace('-', '').replace(' ', '')

    if len(cpf) != 11 or not cpf.isdigit():
       return jsonify({'status': 'error', 'mensagem': 'CPF inválido'}), 400
    
#-----------------------------
#      CONSULTAR DADOS 
#-----------------------------
def obter_dados():
    dados = request.get_json()
    return dados
    
def cpf_enviado():
    obter_dados
    cpf = dados.get('cpf')
    return cpf
#-----------------------------
#    CONSULTAR USUÁRIO
#-----------------------------

@app.route('/usuario/login', methods=['POST'])
def consultar_usuario(): 

    obter_dados()
    cpf_enviado()
    senha_digitada = dados.get('senha')

    validarCPF()

    values_cpf = [cpf]
    # Verifica se existe cadastro
    query_cpf = 'select count(*) from rh where cpf = %s;'
    linhas_afetadas = consultarBancoDados(conexao, query_cpf, values_cpf)

    if linhas_afetadas > 0:
        
        query_validar_senha = 'select (senha_hash) from senha where cpf = %s'
        senha_banco = listarBancoDados(conexao, query_validar_senha,values_cpf )
        
        senha_hash = senha_banco[0][0]
       
        if bcrypt.checkpw(
            senha_digitada.encode(),
            senha_hash.encode
        ):
            query_nome_cliente = 'select (nome) from rh where cpf = %s'
            procurar_nome_do_cliente = listarBancoDados(conexao, query_nome_cliente, [cpf])
            nome = procurar_nome_do_cliente[0][0]

            return {
                'status': 'login concluido',
                'cpf': cpf,
                'nome': nome,
                'senha': senha_hash
                }, 200

        else:
            return {
                'status': 'senha incorreta',
            }, 404

    else:
        return {
            'status': 'nao_encontrado',
            'cpf': cpf
        }, 404

# -----------------------------
#    CADASTRAR USUÁRIO
# -----------------------------

@app.route('/usuario/cadastro', methods=['POST'])
def cadastrar_usuario():

    obter_dados()
    cpf_enviado()
    nome = dados.get('nome')
    senha = dados.get('senha')

    validarCPF()

    values = [cpf, nome]
    values_senha = [cpf, senha]

    try:
        query_cpf = 'INSERT INTO rh (cpf,nome) VALUES (%s, %s);'
        insertNoBancoDados(conexao, query_cpf, values)

        query_senha = 'INSERT INTO senha (cpf, senha_hash) VALUES (%s, SHA2(%s, 256));'
        insertNoBancoDados(conexao, query_senha, values_senha)

        conexao.commit()

        return jsonify({
            'status': 'criado',
            'cpf': cpf_enviado(),
            'nome': nome,
            'senha': senha
        }), 201

    except Exception as e:
        conexao.rollback()
        
        return jsonify({
            'status': 'error',
            'mensagem': str(e)
        }), 500

# -----------------------------
#    CADASTRAR RECLAMAÇÃO
# -----------------------------

@app.route('usuario/reclamacao', methods=['POST'])
def obter_reclamacao():
    
    obter_dados()
    cpf_enviado()
    reclamacao = dados.get('reclamacao')
    
    values_cpf = cpf_enviado
    values_reclamacao = [reclamacao]
    query_reclamacao = 'INSERT INTO reclamacoes(cpf, descricao) VALUES (%s, %s)'

    try:
        insertNoBancoDados(conexao, query_reclamacao, values_cpf + values_reclamacao)
        conexao.commit()
  

        return jsonfy({
            'status': 'reclamacao criada',
            'cpf': cpf_enviado
        })