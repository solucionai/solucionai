# from flask import Flask, request, jsonify
# import requests
# app = Flask(__name__)

# # Variável global para armazenar os dados
# stored_data = None

# @app.route('/store', methods=['POST'])
# def store_data():
#     global stored_data
#     # Obtém os dados JSON da solicitação
#     data = request.get_json()
#     print(data)
    
#     if not data:
#         return jsonify({'error': 'No data provided'}), 400
    
#     # Armazena os dados recebidos
#     stored_data = data
    

#     ### requisição pra mudar os dados do botconversa


#     # URL do webhook
#     url = "https://backend.botconversa.com.br/api/v1/webhooks-automation/catch/117619/DyztDujcvKUx/"

#     # Payload padrão com nome, número de celular e resposta_prompt
#     payload = {
#         "name": "gustavo zitta",
#         "phone_number": "+556186421816",
#         "resposta_prompt": "gustavao",
#         "docs" : "testando docs"
#     }

#     # Cabeçalhos (se necessário)
#     headers = {
#         "Content-Type": "application/json"
#     }

#     # Enviando o payload para a URL especificada
#     response = requests.post(url, json=payload, headers=headers)

#     # Verificando a resposta
#     if response.status_code == 200:
#         print("Payload enviado com sucesso!")
#     else:
#         print(f"Falha ao enviar payload. Status code: {response.status_code}")
#         print(f"Resposta: {response.text}")

        




#     return jsonify({'message': 'Data stored successfully'}), 200



# if __name__ == '__main__':
#     app.run(debug=True, port=8000)


# from flask import Flask, request, jsonify
# from pymongo import MongoClient

# app = Flask(__name__)

# # Configuração da conexão com o MongoDB
# client = MongoClient('mongodb://localhost:27017/')
# db = client['seu_banco_de_dados']
# collection = db['sua_colecao']

# @app.route('/store', methods=['POST'])
# def store_data():
#     # Obtém os dados JSON da solicitação
#     data = request.get_json()
#     print(data)
    
#     if not data:
#         return jsonify({'error': 'No data provided'}), 400

#     numero_wpp = data.get('numero_wpp')
    
#     if not numero_wpp:
#         return jsonify({'error': 'Field "numero_wpp" is required'}), 400
    
#     # Verifica se o documento com o numero_wpp já existe e atualiza ou insere
#     collection.update_one(
#         {'numero_wpp': numero_wpp},  # Filtro para encontrar o documento
#         {'$set': data},  # Dados a serem atualizados/adicionados
#         upsert=True  # Se não encontrar, insere um novo documento
#     )
    
#     return jsonify({'status': 'Data stored successfully'})

# if __name__ == '__main__':
#     app.run(debug=True, port=8000)


from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

# Configuração da conexão com o MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['seu_banco_de_dados']
collection = db['sua_colecao']

@app.route('/store', methods=['POST'])
def store_data():
    # Obtém os dados JSON da solicitação
    data = request.get_json()
    print(data)
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    numero_wpp = data.get('numero_wpp')
    
    if not numero_wpp:
        return jsonify({'error': 'Field "numero_wpp" is required'}), 400
    
    # Adiciona ou atualiza os timestamps
    now = datetime.utcnow()
    existing_document = collection.find_one({'numero_wpp': numero_wpp})
    
    if existing_document:
        data['last_modified'] = now
    else:
        data['created_at'] = now
        data['last_modified'] = now
    
    # Verifica se o documento com o numero_wpp já existe e atualiza ou insere
    collection.update_one(
        {'numero_wpp': numero_wpp},  # Filtro para encontrar o documento
        {'$set': data},  # Dados a serem atualizados/adicionados
        upsert=True  # Se não encontrar, insere um novo documento
    )
    
    return jsonify({'status': 'Data stored successfully'})

if __name__ == '__main__':
    app.run(debug=True, port=8000)