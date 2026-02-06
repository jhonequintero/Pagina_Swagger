import secrets
import os
import pyodbc
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from datetime import datetime, timedelta

# --- Configuración de la base de datos ---
# Importante: No uses doble llave {{}} aquí, pyodbc en Linux es estricto
DB_SERVER = os.environ.get("DB_SERVER", "192.168.1.16")
DB_NAME = os.environ.get("DB_NAME", "ETL")
DB_USER = os.environ.get("DB_USER", "integraciones")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "c**") 

# El driver debe ir sin llaves aquí, se las ponemos solo una vez en la cadena
DRIVER_VERSION = 'ODBC Driver 17 for SQL Server'

# Cadena de conexión limpia para Linux/Render
CONN_STRING = (
    f"DRIVER={{{DRIVER_VERSION}}};" 
    f"SERVER={DB_SERVER};"
    f"DATABASE={DB_NAME};"
    f"UID={DB_USER};"
    f"PWD={DB_PASSWORD};"
    "Encrypt=yes;"
    "TrustServerCertificate=yes;"
    "Connection Timeout=30;"
)

def get_connection():
    # Retornamos la conexión con timeout aumentado para red externa
    return pyodbc.connect(CONN_STRING, timeout=30)

# --- Encabezado API ---
app = FastAPI(
    title="Api Jhoneider Quintero",
    version="v1",
    docs_url="/",
    openapi_url="/swagger/v1/swagger.json"
)

security = HTTPBearer()
tokens_con_vencimiento = {}

# --- Modelos ---
class LoginRequest(BaseModel):
    username: str
    password: str

# Modelo para el POST de Clientes
class ClienteNuevo(BaseModel):
    documento: str
    cupoOtorgado: float
    nombres: str
    apellidos: str
    email: str

# --- Validar token ---
def validar_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token_recibido = credentials.credentials
    if token_recibido.startswith("Bearer "):
        token_recibido = token_recibido.replace("Bearer ", "").strip()
    
    ahora = datetime.now()
    if token_recibido not in tokens_con_vencimiento or ahora > tokens_con_vencimiento[token_recibido]:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    return True

# --- Autenticar ---
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

# --- Métodos Bdatam ---

@app.post("/api/Bdatam/CreateCustomer", tags=["Bdatam"], summary="Registrar nuevo cliente")
def create_customer(cliente: ClienteNuevo, auth=Depends(validar_token)):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        # Llamamos al procedimiento que inserta
        cursor.execute("{CALL sp_InsertarClientePrueba (?, ?, ?, ?, ?)}", 
                       (cliente.documento, cliente.cupoOtorgado, cliente.nombres, cliente.apellidos, cliente.email))
        conn.commit()
        return {"succeeded": True, "message": "Cliente guardado exitosamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar: {str(e)}")
    finally:
        if 'conn' in locals(): conn.close()

@app.get("/api/Bdatam/GetCustomersBDAtambById", tags=["Bdatam"])
def get_customer(id: str, auth=Depends(validar_token)):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("{CALL sp_ConsultarClientePrueba (?)}", id)
        row = cursor.fetchone()
        
        if row:
            columnas = [column[0] for column in cursor.description]
            return dict(zip(columnas, row))
        
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        if 'conn' in locals(): conn.close()

@app.get("/api/Bdatam/GetAllCustomers", tags=["Bdatam"])
def get_all_customers(auth=Depends(validar_token)):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("{CALL sp_ConsultarTodosClientes}")
        rows = cursor.fetchall()
        
        if rows:
            columnas = [column[0] for column in cursor.description]
            return {"succeeded": True, "data": [dict(zip(columnas, r)) for r in rows]}
        
        return {"succeeded": False, "message": "No hay datos"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        if 'conn' in locals(): conn.close()