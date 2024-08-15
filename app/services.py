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
        # Conecte-se ao banco de dados 'test'
        db = client['test']
        
        # Conecte-se à coleção 'solucionai_clientes'
        collection = db['solucionai_clientes']
        
        # Testa a conexão
        server_info = client.server_info()  # Isso lançará uma exceção se a conexão falhar
        print("Conectado ao MongoDB com sucesso.")
        
        # Retorna o objeto da coleção para ser usado em outras partes do aplicativo
        return collection
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
        # Update RAW_DATA with existing data and new data
        existing_raw_data = existing_document.get('RAW_DATA', {})
        updated_raw_data = {**existing_raw_data, **data}
        data['RAW_DATA'] = updated_raw_data
        new_id = existing_document.get('id')  # Use the existing id for return
    else:
        # Get the last ID and increment it by 1
        last_user = collection.find_one(sort=[('id', -1)])  # Sort by 'id' in descending order
        new_id = (last_user['id'] + 1) if last_user else 1
        data['id'] = new_id  # Assign new ID
        
        data['created_at'] = now
        data['last_modified'] = now
        data['RAW_DATA'] = data.copy()  # Initialize RAW_DATA with the current data
    
    # Remove 'RAW_DATA' from the main data to avoid duplication
    raw_data_to_store = data.pop('RAW_DATA')
    
    # Update or insert document
    try:
        result = collection.update_one(
            {'numero_wpp': numero_wpp},  # Filter to find the document
            {'$set': data, '$setOnInsert': {'RAW_DATA': raw_data_to_store}},  # Data to update/add
            upsert=True  # If not found, insert a new document
        )
        
        # Update RAW_DATA separately to avoid overwriting during upsert
        if existing_document:
            result = collection.update_one(
                {'numero_wpp': numero_wpp},
                {'$set': {'RAW_DATA': raw_data_to_store}}
            )
        
        logging.info(f"Document updated/inserted successfully: {result}")
        return {'status': 'Data stored successfully', 'id': new_id}, 200
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
