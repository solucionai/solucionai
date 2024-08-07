from pymongo import MongoClient, errors
from datetime import datetime
import logging
import os
from bson import ObjectId

# Setup logging
logging.basicConfig(level=logging.INFO)






def init_db():
    connection_url = "mongodb://mongo:juzfrgHjdNilrrIVybaxVJrBLLRLTKrp@viaduct.proxy.rlwy.net:25989"
    client = MongoClient(connection_url)
    
    try:
        # Conecte-se ao banco de dados específico se desejar
        db = client['nome_do_banco_de_dados']
        
        # Testa a conexão
        server_info = client.server_info()  # Isso lançará uma exceção se a conexão falhar
        print("Conectado ao MongoDB com sucesso.")
        
        # Retorna o objeto do banco de dados para ser usado em outras partes do aplicativo
        return db
    except Exception as e:
        print(f"Erro ao conectar ao MongoDB: {e}")
        return None

collection = init_db()

def store_data(data):
    if not data:
        logging.warning("No data provided in the request")
        return {'error': 'No data provided'}, 400

    numero_wpp = data.get('numero_wpp')
    
    if not numero_wpp:
        logging.warning('Field "numero_wpp" is required in the request')
        return {'error': 'Field "numero_wpp" is required'}, 400
    
    # Add or update timestamps
    now = datetime.utcnow()
    existing_document = collection.find_one({'numero_wpp': numero_wpp})
    
    if existing_document:
        data['last_modified'] = now
    else:
        data['created_at'] = now
        data['last_modified'] = now
    
    # Update or insert document
    try:
        result = collection.update_one(
            {'numero_wpp': numero_wpp},  # Filter to find the document
            {'$set': data},  # Data to update/add
            upsert=True  # If not found, insert a new document
        )
        logging.info(f"Document updated/inserted successfully: {result}")
        return {'status': 'Data stored successfully'}, 200
    except errors.PyMongoError as e:
        logging.error(f"Failed to store data in MongoDB: {e}")
        return {'error': 'Failed to store data'}, 500

def get_data(numero_wpp):
    try:
        document = collection.find_one({'numero_wpp': numero_wpp})
        if not document:
            logging.warning(f"No document found with numero_wpp: {numero_wpp}")
            return {'error': 'Document not found'}, 404

        # Convert ObjectId to string
        document['_id'] = str(document['_id'])
        
        logging.info(f"Document retrieved successfully: {document}")
        return document, 200
    except errors.PyMongoError as e:
        logging.error(f"Failed to retrieve data from MongoDB: {e}")
        return {'error': 'Failed to retrieve data'}, 500

def get_all_data():
    try:
        documents = list(collection.find({}))
        if not documents:
            logging.warning("No documents found in the collection")
            return {'error': 'No documents found'}, 404

        # Convert ObjectId to string for each document
        for document in documents:
            document['_id'] = str(document['_id'])

        logging.info(f"{len(documents)} documents retrieved successfully")
        return documents, 200
    except errors.PyMongoError as e:
        logging.error(f"Failed to retrieve data from MongoDB: {e}")
        return {'error': 'Failed to retrieve data'}, 500
