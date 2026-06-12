import os 
from metodos_conexao import *
from flask import Flask, request, jsonify 

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
#    CONSULTAR USUÁRIO
#-----------------------------

@app.route('/usuario', methods=['POST'])
def consultar_usuario(): #Essa função tem o objetivo de consultar o CPF do usuário, caso ele não tenha cadastro encaminha ele para fazer o cadastro.

    dados = request.json()
    cpf = dados.get('cpf')

    validarCPF()

    # Verifica se existe cadastro
    query_cpf = 'select count(*) from rh where cpf = %s;'
    linhas_afetadas = consultarBancoDados(conexao, query_cpf, [cpf])

    if linhas_afetadas > 0:
        query_nome_cliente = 'select (nome) from rh where cpf = %s'
        procurar_nome_do_cliente = listarBancoDados(conexao, query_nome_cliente, [cpf])
        nome = procurar_nome_do_cliente[0][0]

        return {
            'status': 'existente',
            'cpf': cpf,
            'nome': nome
        }


    else:
        return {
            'status': 'nao_encontrado',
            'cpf': cpf
        }




