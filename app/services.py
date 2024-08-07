from pymongo import MongoClient, errors
from datetime import datetime
import logging
import os
from bson import ObjectId

# Setup logging
logging.basicConfig(level=logging.INFO)


# Use as credenciais e o host do Railway
MONGO_HOST = "mongodb.railway.internal"
MONGO_PORT = 27017
MONGO_USER = "mongo"
MONGO_PASSWORD = "juzfrgHjdNilrrIVybaxVJrBLLRLTKrp"
DATABASE_NAME = "your_database"

# Cria a URL de conexão com as credenciais
connection_string = f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/{DATABASE_NAME}"

# Conecta ao MongoDB
client = MongoClient(connection_string)
db = client[DATABASE_NAME]


# Initialize database connection
def init_db():
    try:
        client = MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        logging.info("Connected to MongoDB successfully")
        return collection
    except errors.ConnectionFailure as e:
        logging.error(f"Failed to connect to MongoDB: {e}")
        raise

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
