import secrets
import os
import pyodbc
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from datetime import datetime, timedelta

# =====================================================
# CONFIGURACIÓN BASE DE DATOS
# =====================================================

DB_SERVER = os.environ.get("DB_SERVER", "192.168.1.16")
DB_NAME = os.environ.get("DB_NAME", "webventas")
DB_USER = os.environ.get("DB_USER", "ccontreras")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "Nova2030*")

DRIVER_VERSION = "ODBC Driver 17 for SQL Server"

CONN_STRING = (
    f"DRIVER={{{DRIVER_VERSION}}};"
    f"SERVER={DB_SERVER};"
    f"DATABASE={DB_NAME};"
    f"UID={DB_USER};"
    f"PWD={DB_PASSWORD};"
    f"TrustServerCertificate=yes;"
)

def get_connection():
    return pyodbc.connect(CONN_STRING, timeout=10)

# =====================================================
# FASTAPI
# =====================================================

app = FastAPI(
    title="Api Jhoneider Quintero",
    version="v1",
    docs_url="/",
    openapi_url="/swagger/v1/swagger.json"
)

security = HTTPBearer()
tokens_con_vencimiento = {}

# =====================================================
# MODELOS
# =====================================================

class LoginRequest(BaseModel):
    username: str
    password: str

# =====================================================
# SEGURIDAD - TOKEN
# =====================================================

def validar_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials

    if token.startswith("Bearer "):
        token = token.replace("Bearer ", "").strip()

    ahora = datetime.now()

    if token not in tokens_con_vencimiento:
        raise HTTPException(status_code=401, detail="Token inválido")

    if ahora > tokens_con_vencimiento[token]:
        del tokens_con_vencimiento[token]
        raise HTTPException(status_code=401, detail="Token expirado")

    return token

# =====================================================
# LOGIN
# =====================================================

@app.post("/api/Authenticate/login", tags=["Authenticate"])
def login(request: LoginRequest):
    if request.username == "Administrador" and request.password == "Quintero1234@":
        vence = datetime.now() + timedelta(hours=3)
        token = secrets.token_urlsafe(120)

        tokens_con_vencimiento[token] = vence

        return {
            "token": token,
            "expiration": vence.strftime("%Y-%m-%dT%H:%M:%SZ")
        }

    raise HTTPException(status_code=401, detail="Credenciales incorrectas")







# =====================================================
# CONSULTA BODEGA - EXISTENCIA
# =====================================================

@app.get("/api/consultas/bodega-existencia", tags=["Consultas"])
def obtener_existencia_bodega(
    sucursal: str,   # CUC
    bodega: str,     # 001
    empresa: str,    # CBB SAS

    token: str = Depends(validar_token)
):
    try:
        # Limpieza básica
        sucursal = sucursal.strip().upper()
        bodega = bodega.strip()
        empresa = empresa.strip().upper()

        # Validaciones de formato (NO negocio)
        if not sucursal.isalpha():
            raise HTTPException(400, "Sucursal debe ser texto (ej: CUC)")

        if not bodega.isdigit():
            raise HTTPException(400, "Bodega debe ser numérica (ej: 001)")

        # Conexión
        conn = get_connection()
        cursor = conn.cursor()

        # 🔥 ORDEN REAL DEL PROCEDIMIENTO
        cursor.execute(
            "EXEC Consulta_Bodega_existencia ?, ?, ?",
            (bodega, sucursal, empresa)
        )

        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()

        # ÚNICA VALIDACIÓN CORRECTA
        if not rows:
            raise HTTPException(
                status_code=404,
                detail="No existen datos para esa combinación"
            )

        data = [dict(zip(columns, row)) for row in rows]

        return {
            "status": "success",
            "total_registros": len(data),
            "data": data
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass


# =====================================================
# CONSULTA BODEGA - LISTAS 
# =====================================================

@app.get("/api/consultas/listas", tags=["Consultas"])
def obtener_listas(
    sucursal: str,   # CUC
    bodega: str,     # 001
    token: str = Depends(validar_token)
):
    try:
        sucursal = sucursal.strip().upper()
        bodega = bodega.strip()

        # Validaciones de formato (no negocio)
        if not sucursal.isalpha():
            raise HTTPException(400, "Sucursal debe ser texto (ej: CUC)")

        if not bodega.isdigit():
            raise HTTPException(400, "Bodega debe ser numérica (ej: 001)")

        conn = get_connection()
        cursor = conn.cursor()

        # ORDEN REAL DEL PROCEDIMIENTO
        cursor.execute(
            "EXEC Consulta_Listas ?, ?",
            (bodega, sucursal)
        )

        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()

        if not rows:
            raise HTTPException(
                status_code=404,
                detail="No existen datos para esa combinación"
            )

        data = [dict(zip(columns, row)) for row in rows]

        return {
            "status": "success",
            "total_registros": len(data),
            "data": data
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass
