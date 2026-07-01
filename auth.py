from dotenv import load_dotenv

import os

import jwt

from flask import request, jsonify

from datetime import datetime, timedelta


load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    raise ValueError("A variável de ambiente SECRET_KEY não está definida.")


def gerar_token(cpf, expiracao_horas=24):
    if not cpf or not isinstance(cpf, str):
        raise ValueError(
            "CPF inválido. Certifique-se de fornecer um CPF válido como string.")
    payload = {
        "cpf": cpf,
        "exp": datetime.utcnow() + timedelta(hours=expiracao_horas)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token


def verificar_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload["cpf"], None

    except jwt.ExpiredSignatureError:
        return None, "Token expirado"

    except jwt.InvalidTokenError:
        return None, "Token inválido"


def token_obrigatorio(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization")
        if not auth or not auth.startswith("Bearer "):
             return jsonify({"error": "Token não fornecido"}), 401
        token = auth.split(" ")[1]
        cpf, error = verificar_token(token)
        if error:
            return jsonify({"error": error}), 401
        return func(cpf, *args, **kwargs)
    return wrapper
