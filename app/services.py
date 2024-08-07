from pymongo import MongoClient, errors
from datetime import datetime
import logging

# Configuração do log
logging.basicConfig(level=logging.INFO)

# Configuração da conexão com o MongoDB
client = None
db = None
collection = None

def init_db():
    global client, db, collection
    try:
        client = MongoClient('mongodb://localhost:27017/')
        db = client['seu_banco_de_dados']
        collection = db['sua_colecao']
        logging.info("Conexão com o MongoDB estabelecida com sucesso")
    except errors.ConnectionFailure as e:
        logging.error(f"Erro de conexão com o MongoDB: {e}")

def store_data(data):
    if not data:
        logging.warning("Nenhum dado fornecido na solicitação")
        return {'error': 'No data provided'}, 400

    numero_wpp = data.get('numero_wpp')
    
    if not numero_wpp:
        logging.warning('Campo "numero_wpp" ausente na solicitação')
        return {'error': 'Field "numero_wpp" is required'}, 400
    
    # Adiciona ou atualiza os timestamps
    now = datetime.utcnow()
    existing_document = collection.find_one({'numero_wpp': numero_wpp})
    
    if existing_document:
        data['last_modified'] = now
    else:
        data['created_at'] = now
        data['last_modified'] = now
    
    # Verifica se o documento com o numero_wpp já existe e atualiza ou insere
    try:
        result = collection.update_one(
            {'numero_wpp': numero_wpp},  # Filtro para encontrar o documento
            {'$set': data},  # Dados a serem atualizados/adicionados
            upsert=True  # Se não encontrar, insere um novo documento
        )
        logging.info(f"Documento atualizado/inserido com sucesso: {result}")
        return {'status': 'Data stored successfully'}, 200
    except errors.PyMongoError as e:
        logging.error(f"Erro ao salvar dados no MongoDB: {e}")
        return {'error': 'Failed to store data'}, 500

# Inicializa a conexão com o banco de dados ao importar o módulo
init_db()
