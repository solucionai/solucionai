
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any
import logging
from app.services import store_data, get_data, get_all_data, clear_data

app = FastAPI()

# Setup logging
logging.basicConfig(level=logging.INFO)

# Data model for the request
class DataModel(BaseModel):
    numero_wpp: str
    outros_campos: Dict[str, Any] = Field(default_factory=dict)  # Dictionary for dynamic fields

    class Config:
        extra = "allow"  # Allow extra fields

@app.post("/store")
async def store_data_endpoint(data: DataModel):
    result, status_code = store_data(data.dict())
    
    if status_code != 200:
        raise HTTPException(status_code=status_code, detail=result['error'])
    
    return result

@app.get("/retrieve/{numero_wpp}")
async def retrieve_data_endpoint(numero_wpp: str):
    result, status_code = get_data(numero_wpp)
    
    if status_code != 200:
        raise HTTPException(status_code=status_code, detail=result['error'])
    
    return result


@app.get("/retrieve_all")
async def retrieve_all_data_endpoint():
    result, status_code = get_all_data()

    if status_code != 200:
        raise HTTPException(status_code=status_code, detail=result['error'])

    return result


@app.route('/add_data', methods=['POST'])
def upload_xlsx():
    if 'file' not in request.files:
        return jsonify({"error": "Nenhum arquivo foi enviado"}), 400

    file = request.files['file']
    return add_data_from_xlsx(file)


@app.delete("/clear_db")
async def clear_db_endpoint():
    result, status_code = clear_data()  # Chamando a função de limpar o banco de dados

    if status_code != 200:
        raise HTTPException(status_code=status_code, detail="Erro ao limpar o banco de dados.")
    
    return {"message": "Banco de dados limpo com sucesso!"}
