import secrets
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from datetime import datetime, timedelta

app = FastAPI(
    title="Api TownCenter",
    version="v1",
    docs_url="/",
    openapi_url="/swagger/v1/swagger.json"
)

security = HTTPBearer()
tokens_con_vencimiento = {}

db_clientes = [
    {
        "documento": "1094050373",
        "cupoOtorgado": 0,
        "cupoDisponible": 0,
        "nombres": "JHONEYDER EMMANUEL",
        "apellidos": "QUINTERO RODRIGUEZ",
        "celular": "3205739029",
        "email": "jhoneiderrodriguez6@gmail.com"
    }
]

class LoginRequest(BaseModel):
    username: str
    password: str
    
    
def validar_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Obtenemos lo que Swagger mandó
    token_recibido = credentials.credentials
    
    # Si el usuario escribió "Bearer " dentro del cuadro, lo limpiamos nosotros
    if token_recibido.startswith("Bearer "):
        token_recibido = token_recibido.replace("Bearer ", "").strip()
    
    ahora = datetime.now()
    
    # Esto te dirá en la consola exactamente qué token estás comparando
    print(f"DEBUG: Comparando token -> {token_recibido[:15]}...")

    if token_recibido not in tokens_con_vencimiento:
        raise HTTPException(status_code=401, detail="Token no encontrado o inválido")
    
    if ahora > tokens_con_vencimiento[token_recibido]:
        del tokens_con_vencimiento[token_recibido]
        raise HTTPException(status_code=401, detail="Token expirado")
        
    return True
@app.post("/api/Authenticate/login", tags=["Authenticate"])
def login(request: LoginRequest):
    if request.username == "Administrador" and request.password == "Quintero1234@":
        vence = datetime.now() + timedelta(hours=3)
        token_aleatorio = secrets.token_urlsafe(120)
        tokens_con_vencimiento[token_aleatorio] = vence
        return {
            "token": token_aleatorio,
            "expiration": vence.strftime("%Y-%m-%dT%H:%M:%SZ")
        }
    raise HTTPException(status_code=401, detail="Credenciales incorrectas")





#traer clientes 
@app.get("/api/Bdatam/GetCustomersBDAtambById", tags=["Bdatam"])
def get_customer(id: str, auth=Depends(validar_token)):
    cliente = next((c for c in db_clientes if c["documento"] == id), None)
    if cliente:
        return cliente
    
    return {
        "succeeded": False,
        "errors": [{"code": "0", "description": "Cliente no encontrado"}]
    }