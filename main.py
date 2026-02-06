import secrets
import os
import pyodbc
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from datetime import datetime, timedelta

# --- Configuración de la base de datos ---
DRIVER_VERSION = "ODBC Driver 17 for SQL Server"
DB_SERVER = os.environ.get("DB_SERVER", "localhost")
DB_NAME = os.environ.get("DB_NAME", "WebApi")
DB_USER = os.environ.get("DB_USER", "sa")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")

CONN_STRING = (
    f"DRIVER={{{DRIVER_VERSION}}};" 
    f"SERVER={DB_SERVER};"
    f"DATABASE={DB_NAME};"
    f"UID={DB_USER};"
    f"PWD={DB_PASSWORD};" # Eliminé los corchetes extra aquí para evitar errores de sintaxis en el PWD
)

def get_connection():
    # Eliminé autocommit=False para que las consultas simples funcionen directo
    return pyodbc.connect(CONN_STRING, timeout=10)

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




# --- Validar token y vencimiento ---
def validar_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token_recibido = credentials.credentials
    
    if token_recibido.startswith("Bearer "):
        token_recibido = token_recibido.replace("Bearer ", "").strip()
    
    ahora = datetime.now()
    print(f"DEBUG: Comparando token -> {token_recibido[:15]}...")

    if token_recibido not in tokens_con_vencimiento:
        raise HTTPException(status_code=401, detail="Token no encontrado o inválido")
    
    if ahora > tokens_con_vencimiento[token_recibido]:
        del tokens_con_vencimiento[token_recibido]
        raise HTTPException(status_code=401, detail="Token expirado")
    return 



# --- Autentificar API ---
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




@app.get("/api/Bdatam/GetCustomersBDAtambById", tags=["Bdatam"])
def get_customer(id: str, auth=Depends(validar_token)):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Ejecutamos tu procedimiento almacenado
        cursor.execute("{CALL sp_ConsultarClientePrueba (?)}", id)
        row = cursor.fetchone()
        
        if row:
            # MAPEO DINÁMICO: Convierte las columnas de la tabla en llaves del JSON
            columnas = [column[0] for column in cursor.description]
            cliente_data = dict(zip(columnas, row))
            return cliente_data
        
        return {
            "succeeded": False, 
            "errors": [{"code": "0", "description": "Cliente no encontrado en WebApi"}]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error de conexión: {str(e)}")
    finally:
        
        if 'conn' in locals():
            conn.close()



@app.get("/api/Bdatam/GetAllCustomers", tags=["Bdatam"], summary="Consultar todos los clientes")
def get_all_customers(auth=Depends(validar_token)):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Ejecutamos el nuevo SP sin parámetros
        cursor.execute("{CALL sp_ConsultarTodosClientes}")
        rows = cursor.fetchall()
        
        # Si hay datos, los mapeamos todos a una lista de diccionarios
        if rows:
            columnas = [column[0] for column in cursor.description]
            # Usamos una lista de comprensión para mapear cada fila
            resultado = [dict(zip(columnas, row)) for row in rows]
            return {
                "succeeded": True,
                "data": resultado
            }
        
        return {
            "succeeded": False, 
            "errors": [{"code": "0", "description": "No hay clientes registrados"}]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

                                                        


    
        
            
                
                    
                        
                            
                                
                                    



                                    
                                
                            
                        
                    
                
            
        
    


                                                        