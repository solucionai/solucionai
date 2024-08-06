
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
