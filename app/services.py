from pymongo import MongoClient, errors
from datetime import datetime
import logging
import os
from bson import ObjectId
from fpdf import FPDF
import tempfile
import requests


# Setup logging
logging.basicConfig(level=logging.INFO)


API_TOKEN = 'bbdd39fba4dab68ac0c03f4a629680f7429478ff'
COMPANY_DOMAIN = 'solucionai'
PIPEDRIVE_URL = f'https://{COMPANY_DOMAIN}.pipedrive.com/api/v1/deals?api_token={API_TOKEN}'




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

def create_pipedrive_deal(deal):
    try:
        response = requests.post(PIPEDRIVE_URL, json=deal)
        response.raise_for_status()
        response_data = response.json()
        
        if response_data.get('success'):
            logging.info(f"Deal was added successfully: {response_data}")
            return response_data['data']['id']
        else:
            logging.error(f"Failed to add deal: {response_data}")
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Request to Pipedrive API failed: {e}")
        return None


def store_data(data):
    if not data:
        logging.warning("No data provided in the request")
        return {'error': 'No data provided'}, 400

    numero_wpp = data.get('numero_wpp')
    problema = data.get('PROBLEMA')
    
    if not numero_wpp:
        logging.warning('Field "numero_wpp" is required in the request')
        return {'error': 'Field "numero_wpp" is required'}, 400
    
    if not problema:
        logging.warning('Field "PROBLEMA" is required in the request')
        return {'error': 'Field "PROBLEMA" is required'}, 400

    now = datetime.utcnow()
    
    # Check if a document with the same numero_wpp and PROBLEMA exists
    existing_document = collection.find_one({'numero_wpp': numero_wpp, 'PROBLEMA': problema})
    
    if existing_document:
        # If it exists, update the existing document
        data['last_modified'] = now
        existing_raw_data = existing_document.get('RAW_DATA', {})
        updated_raw_data = {**existing_raw_data, **data}
        data['RAW_DATA'] = updated_raw_data
        new_id = existing_document.get('id')  # Use the existing id for return
    else:
        # If not, count total documents to set new deal_id
        total_documents = collection.count_documents({})
        deal_id = total_documents + 1  # Calculate the deal_id based on the total number of documents
        
        # Create a new document with the new deal_id
        data['deal_id'] = deal_id  # Set the new deal_id
        data['created_at'] = now
        data['last_modified'] = now
        data['RAW_DATA'] = data.copy()  # Initialize RAW_DATA with the current data

        # Create a new deal in Pipedrive
        deal = {
            'title': f'problema - {numero_wpp}',
            'org_id': None,  # Optional: If you have an organization ID
            'value': 10000,  # Example value, you may want to customize this
            'currency': 'USD',
            'user_id': None,
            'person_id': None,  # You can pass the user ID if available
            'stage_id': 1,  # Customize stage ID based on your pipeline
            'status': 'open',
            'expected_close_date': now.strftime('%Y-%m-%d'),
            'probability': 60,
            'lost_reason': None,
            'visible_to': 1,
            'add_time': now.strftime('%Y-%m-%d')
        }

        pipedrive_deal_id = create_pipedrive_deal(deal)
        if pipedrive_deal_id:
            data['pipedrive_deal_id'] = pipedrive_deal_id

    raw_data_to_store = data.pop('RAW_DATA')
    
    try:
        # Upsert logic based on whether the document already exists
        result = collection.update_one(
            {'numero_wpp': numero_wpp, 'PROBLEMA': problema},  # Filter by numero_wpp and PROBLEMA
            {'$set': data, '$setOnInsert': {'RAW_DATA': raw_data_to_store}},  # Update or insert RAW_DATA
            upsert=True  # Insert a new document if no match is found
        )
        
        if existing_document:
            result = collection.update_one(
                {'numero_wpp': numero_wpp, 'PROBLEMA': problema},
                {'$set': {'RAW_DATA': raw_data_to_store}}
            )
        
        logging.info(f"Document updated/inserted successfully: {result}")
        
        # Call the function to generate PDF and upload
        try:
            save_data_as_pdf_and_upload(data, new_id if existing_document else deal_id, 27, 12)
            logging.info("PDF generated and uploaded successfully.")
        except Exception as e:
            logging.error(f"Failed to generate or upload PDF: {e}")
            return {'status': 'Data stored but failed to generate/upload PDF', 'deal_id': new_id if existing_document else deal_id}, 500
        
        return {'status': 'Data stored successfully and PDF uploaded', 'deal_id': new_id if existing_document else deal_id}, 200
        
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



def save_data_as_pdf_and_upload(data, deal_id, person_id, org_id):
    try:
        # Criação do objeto FPDF
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        # Configurações do título e estilo
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt="Dados do Request", ln=True, align="C")

        # Adiciona os dados ao PDF
        pdf.set_font("Arial", size=10)

        for key, value in data.items():
            pdf.cell(200, 10, txt=f"{key}: {value}", ln=True)

        # Criação de um arquivo temporário para salvar o PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            pdf_output_path = temp_file.name
            pdf.output(pdf_output_path)

        # Agora, vamos fazer o upload do arquivo PDF para o endpoint
        api_token = '30ecee2f9e8872664a17adfd33fa7c018cd49f2f'
        company_domain = 'solucionai2'

        # Construa a URL
        url = f'https://{company_domain}.pipedrive.com/api/v1/files?api_token={api_token}'

        # Payload com os IDs
        payload = {
            'deal_id': deal_id,
            'person_id': person_id,
            'org_id': org_id,
        }
        print('*******')
        print(deal_id)
        # Headers
        headers = {
            'Accept': 'application/json'
        }

        # Upload do arquivo usando um bloco try-except
        try:
            with open(pdf_output_path, 'rb') as pdf_file:
                files = {
                    'file': ('data.pdf', pdf_file, 'application/pdf')
                }
                response = requests.post(url, headers=headers, data=payload, files=files)

                # Verifica se o upload foi bem-sucedido
                if response.status_code == 201:
                    print("Upload bem-sucedido")
                else:
                    print(f"Falha no upload: {response.status_code} - {response.text}")
                    raise Exception(f"Erro no upload: {response.status_code}")
        except requests.RequestException as e:
            print(f"Erro de requisição: {e}")
            raise Exception(f"Erro de rede ao tentar fazer o upload: {str(e)}")
        except Exception as e:
            print(f"Erro inesperado durante o upload: {e}")
            raise e
        finally:
            # Remover o arquivo temporário após o upload
            if os.path.exists(pdf_output_path):
                os.remove(pdf_output_path)

        return pdf_output_path

    except Exception as e:
        print(f"Ocorreu um erro ao criar ou enviar o PDF: {e}")
        raise e



# Função para adicionar dados a partir de um arquivo XLSX
def add_data_from_xlsx(file):
    try:
        # Inicializa a conexão com a coleção
        collection = init_db()

        # Faz o upload do arquivo e lê o conteúdo usando pandas
        file_path = secure_filename(file.filename)
        file.save(file_path)
        
        # Lê o arquivo XLSX em um DataFrame do pandas
        data = pd.read_excel(file_path)
        
        # Converte o DataFrame em uma lista de dicionários para inserir no MongoDB
        records = data.to_dict(orient='records')

        # Insere os dados na coleção MongoDB
        result = collection.insert_many(records)
        
        return {"message": f"{len(result.inserted_ids)} documentos adicionados com sucesso."}, 200
    except Exception as e:
        # Retorna uma mensagem de erro em caso de exceção
        return {"error": str(e)}, 500




# Função para limpar todos os dados da coleção
def clear_data():
    try:
        collection = init_db()  # Inicializa a conexão e obtém a coleção
        result = collection.delete_many({})  # Deleta todos os documentos da coleção
        
        # Verifica se a operação foi bem-sucedida
        if result.deleted_count > 0:
            return {"message": f"{result.deleted_count} documentos deletados com sucesso."}, 200
        else:
            return {"message": "Nenhum documento encontrado para deletar."}, 200
    except Exception as e:
        # Caso haja algum erro durante a operação
        return {"error": str(e)}, 500
