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

app = Flask(__name__)

#-----------------------------
#    VALIDAÇÃO DO CPF
#-----------------------------

def validarCPF():
    dados = request.get_json()
    cpf = dados.get('cpf')
    if not cpf:
        return jsonify({'status': 'error', 'mensagem': 'CPF não enviado'}), 400

    cpf = cpf.replace('.', '').replace('-', '').replace(' ', '')

    if len(cpf) != 11 or not cpf.isdigit():
       return jsonify({'status': 'error', 'mensagem': 'CPF inválido'}), 400
    
#-----------------------------
#      CONSULTAR DADOS 
#-----------------------------
def tratar_dados():
    dados = request.get_json()
    if not dados:
        return jsonify({
            'status': 'error',
            'mensagem': 'Nenhum dado enviado para atualização'
        }), 400
    return dados
    

def cpf_enviado():
    dados = tratar_dados()
    cpf = dados.get('cpf')
    return cpf


#-----------------------------
#    CONSULTAR USUÁRIO
#-----------------------------

@app.route('/usuario/login', methods=['POST'])
def consultar_usuario(): 

    dados = obter_dados()
    cpf = cpf_enviado()

    senha_digitada = dados.get('senha')
    
    validarCPF()

    values_cpf = [cpf]
    query_cpf = 'select count(*) from rh where cpf = %s;'
    linhas_afetadas = consultarBancoDados(conexao, query_cpf, values_cpf)

    if linhas_afetadas > 0:
        
        query_validar_senha = 'select (senha_hash) from senha where cpf = %s'
        senha_banco = listarBancoDados(conexao, query_validar_senha,values_cpf )
        
        senha_hash = senha_banco[0][0]
       
        if bcrypt.checkpw(
            senha_digitada.encode(),
            senha_hash.encode()
        ):
            query_nome_cliente = 'select (nome) from rh where cpf = %s'
            procurar_nome_do_cliente = listarBancoDados(conexao, query_nome_cliente, [cpf])
            nome = procurar_nome_do_cliente[0][0]

            return jsonify({
                'status': 'login concluido',
                'cpf': cpf,
                'nome': nome,
                'senha': senha_hash
                }), 200

        else:
            return jsonify ({
                'status': 'senha incorreta',
            }), 404

    else:
        return jsonify ({
            'status': 'nao_encontrado',
            'cpf': cpf
        }), 404

# -----------------------------
#    CADASTRAR USUÁRIO
# -----------------------------

@app.route('/usuario/cadastro', methods=['POST'])
def cadastrar_usuario():

    dados = obter_dados()
    cpf = cpf_enviado()
    nome = dados.get('nome')
    senha = dados.get('senha')


    senha_hash = bcrypt.hashpw(
    senha.encode(),
    bcrypt.gensalt()
).decode()
   
    validarCPF()

    values = [cpf, nome]
    values_senha = [cpf, senha]

    try:
        query_cpf = 'INSERT INTO rh (cpf,nome) VALUES (%s, %s);'
        insertNoBancoDados(conexao, query_cpf, values)

        query_senha = 'INSERT INTO senha (cpf, senha_hash) VALUES (%s, %s);'
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

@app.route('/usuario/reclamacao', methods=['POST'])
def obter_reclamacao():
    
    dados = obter_dados()
    cpf = cpf_enviado()
    reclamacao = dados.get('reclamacao')
    
    values_cpf = cpf
    values_reclamacao = [reclamacao]
    query_reclamacao = 'INSERT INTO reclamacoes(cpf, descricao) VALUES (%s, %s)'

    try:
        insertNoBancoDados(conexao, query_reclamacao, values_cpf + values_reclamacao)
        conexao.commit()
  

        return jsonify({
            'status': 'reclamacao criada',
            'cpf': cpf
        }), 201
    
    except Exception as e:
        conexao.rollback()

        return jsonify({
            'status': 'error',
            'mensagem': str(e)
        }), 500
    
# -----------------------------
#    ACOMPANHAR RECLAMAÇÕES
# -----------------------------

@app.route('/relatorio/reclamaçao', methods=['GET'])
def listar_Reclamacoes():

    dados = obter_dados()
    cpf = cpf_enviado()

    values_cpf = [cpf]
    query_listar_reclamacao = 'SELECT descricao FROM RECLAMACOES WHERE cpf = (%s)'

    try:
        listarBancoDados(conexao, query_listar_reclamacao, values_cpf)
        
        return jsonify ({
            'status': 'ok',
            'cpf': cpf
        }), 200
    
    except Exception as e:

        return jsonify({
            'status': 'error',
            'mensagem': str(e)
        }), 204

# -----------------------------
#  ACOMPANHAR RECLAMAÇÕES(id)
# -----------------------------

@app.route('/relatorio/<int:id_reclamacao>', methods=['GET'])
def acompanhar_reclamacao(id_reclamacao):

    values_id = [id_reclamacao]
    query_acompanhar_reclamacao = 'SELECT descricao FROM reclamacoes WHERE id = (%s)'

    try:
        listarBancoDados(conexao, query_acompanhar_reclamacao, values_id)
        
        return jsonify({
            'status': 'ok',
            'id_reclamacao': id_reclamacao
        }), 200
    
    except Exception as e:
        
        return jsonify({
            'status': 'reclamacao nao encontrada',
            'mensagem': str(e)
        }), 404
    
# -----------------------------
#  ATUALIZAR RECLAMAÇÃO(id)
# -----------------------------

@app.route('/reclamacao/<int:id_reclamacao>', methods=['PATCH'])
def atualizar_reclamacao(id_reclamacao):

    dados = tratar_dados()
    nova_descricao = dados.get('nova_descricao')
    
    if not nova_descricao:
        return jsonify({
            'status': 'error',
            'mensagem': 'Nova descrição não enviada'
        }), 400

    values_id = [id_reclamacao]
    values_nova_descricao = [nova_descricao]
    query_atualizar_reclamacao = 'UPDATE reclamacoes SET descricao = (%s) WHERE id = (%s)'

    try:
        linhas_afetadas = atualizarBancoDados(conexao, query_atualizar_reclamacao, values_nova_descricao + values_id)
        
        if linhas_afetadas == 0:
            return jsonify({
                'status' : 'reclamacao nao encontrada',
                'id_reclamacao': id_reclamacao
            }), 404


        return jsonify({
            'status': 'reclamacao atualizada',
            'id_reclamcao': id_reclamacao,
            'nova_descricao': nova_descricao     
        }), 200
    
    except Exception as e:
        
        return jsonify({
            'status': 'error',
            'mensagem': str(e)
        }), 500
    
