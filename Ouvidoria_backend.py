import os
from metodos_conexao import *
from flask import Flask, request, jsonify
import bcrypt

# -----------------------------
#    CONEXÃO COM O SGBD
# -----------------------------

conexao = criarConexao(
    os.getenv("DB_HOST"),
    os.getenv("DB_USER"),
    os.getenv("DB_PASSWORD"),
    os.getenv("DB_NAME")
)

app = Flask(__name__)


@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "api funcionando"}), 200
# -----------------------------
#    VALIDAÇÃO DO CPF
# -----------------------------


def validarCPF():
    dados = request.get_json()
    cpf = dados.get('cpf')
    if not cpf:
        erro = jsonify({'status': 'error', 'mensagem': 'CPF não enviado'}), 400
        return None, erro

    cpf = cpf.replace('.', '').replace('-', '').replace(' ', '')

    if len(cpf) != 11 or not cpf.isdigit():
        erro = jsonify({'status': 'error', 'mensagem': 'CPF inválido'}), 400
        return None, erro

    return cpf, None
# -----------------------------
#      CONSULTAR DADOS
# -----------------------------


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


def autenticar_usuario(cpf, senha_digitada):
    values_CPF = [cpf]
    query_senha_cpf = 'SELECT rh.nome, senha.senha_hash FROM rh INNER JOIN senha ON rh.cpf = senha.cpf WHERE rh.cpf = %s'
    usuario = listarBancoDados(conexao, query_senha_cpf, values_CPF)
    if not usuario:
        erro =  jsonify({
            'status': 'nao_encontrado',
            'cpf': cpf
        }), 404
        return None, erro

    nome, senha_hash = usuario[0]

    if bcrypt.checkpw(
        senha_digitada.encode(),
        senha_hash.encode()
    ):

        return jsonify({
            'status': 'login concluido',
            'cpf': cpf,
            'nome': nome,
        }), 200

    erro = jsonify({
        'status': 'senha incorreta',
    }), 404
    return None, erro
# -----------------------------
#    CONSULTAR USUÁRIO
# -----------------------------


@app.route('/usuario/login', methods=['POST'])
def consultar_usuario():

    dados = tratar_dados()
    cpf = cpf_enviado()
    senha_digitada = dados.get('senha')

    cpf, erro = validarCPF()
    if erro:
        return erro

    usuario, erro = autenticar_usuario(cpf, senha_digitada)
    if erro:
        return erro
    
    return usuario
# -----------------------------
#    CADASTRAR USUÁRIO
# -----------------------------


@app.route('/usuario/cadastro', methods=['POST'])
def cadastrar_usuario():

    dados = tratar_dados()
    cpf = cpf_enviado()
    nome = dados.get('nome')
    senha = dados.get('senha')

    cpf, erro = validarCPF()
    if erro:
        return erro

    senha_hash = bcrypt.hashpw(
        senha.encode(),
        bcrypt.gensalt()
    ).decode()

    values = [cpf, nome]
    values_senha = [cpf, senha_hash]

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
            'senha': senha_hash
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

    dados = tratar_dados()
    cpf = cpf_enviado()
    reclamacao = dados.get('reclamacao')

    values_cpf = [cpf]
    values_reclamacao = [reclamacao]
    query_reclamacao = 'INSERT INTO reclamacoes(cpf, descricao) VALUES (%s, %s)'

    try:
        insertNoBancoDados(conexao, query_reclamacao,
                           values_cpf + values_reclamacao)
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


@app.route('/quantidade/reclamacao', methods=['GET'])
def listar_Reclamacoes():

    dados = tratar_dados()
    cpf = cpf_enviado()

    values_cpf = [cpf]
    query_listar_reclamacao = 'SELECT id, descricao FROM RECLAMACOES WHERE cpf = (%s)'

    try:
        reclamacao = listarBancoDados(
            conexao, query_listar_reclamacao, values_cpf)
        return jsonify({
            'status': 'ok',
            'cpf': cpf,
            'reclamacao': [
                {
                    'id': descricao[0],
                    'descricao': descricao[1]
                }
                for descricao in reclamacao
            ]
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'mensagem': str(e)
        }), 204

# -----------------------------
#  ACOMPANHAR RECLAMAÇÕES(id)
# -----------------------------


@app.route('/reclamacao/<int:id_reclamacao>', methods=['GET'])
def acompanhar_reclamacao(id_reclamacao):

    query_acompanhar_reclamacao = 'SELECT descricao FROM reclamacoes WHERE id = (%s)'
    values_id = [id_reclamacao]

    if not values_id:
        return jsonify({
            'status': 'error',
            'mensagem': 'ID da reclamação não enviado'
        }), 400

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
    cpf = cpf_enviado()
    nova_descricao = dados.get('nova_descricao')

    if not nova_descricao:
        return jsonify({
            'status': 'error',
            'mensagem': 'Nova descrição não enviada'
        }), 400

    values = [nova_descricao, cpf, id_reclamacao]
    query_atualizar_reclamacao = 'UPDATE reclamacoes SET descricao = (%s) WHERE cpf = (%s) AND id = (%s)'

    try:
        linhas_afetadas = atualizarBancoDados(
            conexao, query_atualizar_reclamacao, values)
        if linhas_afetadas == 0:
            return jsonify({
                'status': 'reclamacao nao encontrada',
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


@app.route('/remover/reclamacao/<int:id_reclamacao>', methods=['DELETE'])
def excluir_reclamacao(id_reclamacao):

    dados = tratar_dados()
    cpf = cpf_enviado()

    if not dados or not cpf:
        return jsonify({
            'status': 'error',
            'mensagem': 'Dados ou CPF não enviados para exclusão'
        })

    values_cpf = [cpf]
    values_id = [id_reclamacao]
    query_excluir_reclamacao = 'DELETE FROM reclamacoes WHERE cpf = (%s) AND id = (%s)'

    try:
        linhas_afetadas = excluirBancoDados(
            conexao, query_excluir_reclamacao, values_id + values_cpf)
        if linhas_afetadas == 0:
            return jsonify({
                'status': 'reclamacao nao encontrada',
                'id_reclamacao': id_reclamacao
            }), 404

        return jsonify({
            'status': 'reclamacao excluida',
            'id_reclamcao': id_reclamacao
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'mensagem': str(e)
        }), 500


def iniciar_sistema():
    app.run(debug=True, port=5001)
