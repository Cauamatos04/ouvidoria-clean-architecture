from flask import request, jsonify
import bcrypt

from database import conexao
from metodos_conexao import (
    insertNoBancoDados,
    listarBancoDados,
    atualizarBancoDados,
    consultarBancoDados,
    excluirBancoDados
)

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

# -----------------------------
#    CONSULTAR USUÁRIO
# -----------------------------


def autenticar_usuario(cpf, senha_digitada):
    values_CPF = [cpf]
    query_senha_cpf = 'SELECT rh.nome, senha.senha_hash FROM rh INNER JOIN senha ON rh.cpf = senha.cpf WHERE rh.cpf = %s'
    usuario = listarBancoDados(conexao, query_senha_cpf, values_CPF)
    if not usuario:
        erro = jsonify({
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
#        CRIAR USUÁRIO
# -----------------------------


def inserir_usuario(cpf, nome, senha_hash):
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
            'cpf': cpf,
            'nome': nome,
        }), 201

    except Exception as e:
        conexao.rollback()

        erro = jsonify({
            'status': 'error',
            'mensagem': str(e)
        }), 500

        return None, erro
    
def criar_reclamacao(cpf, reclamacao):
    values = [cpf, reclamacao]
    query_reclamacao = 'INSERT INTO reclamacoes(cpf, descricao) VALUES (%s, %s)'

    try:
        insertNoBancoDados(conexao, query_reclamacao, values)
        conexao.commit()

        return jsonify({
            'status': 'reclamacao criada',
            'cpf': cpf
        }), 201

    except Exception as e:
        conexao.rollback()
        
        erro =  jsonify({
            'status': 'error',
            'mensagem': str(e)
        }), 500
        return None, erro