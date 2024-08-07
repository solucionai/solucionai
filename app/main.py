from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any
import logging
from services import store_data

app = FastAPI()

# Modelo de dados para a solicitação
class DataModel(BaseModel):
    numero_wpp: str
    outros_campos: Dict[str, Any]  # Dicionário para campos dinâmicos

@app.post("/store")
async def store_data_endpoint(request: Request):
    data = await request.json()
    result, status_code = store_data(data)
    
    if status_code != 200:
        raise HTTPException(status_code=status_code, detail=result['error'])
    
    return result

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
