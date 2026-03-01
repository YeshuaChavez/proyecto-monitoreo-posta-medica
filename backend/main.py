"""
=============================================================
 MONITOR IoT — POSTA MÉDICA
 UNMSM FISI 2026
=============================================================
"""

import asyncio
import json
import os
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import SessionLocal, init_db
from models import Suero, Vitales, Alerta, Config, Usuario, Paciente
from mqtt_client import MQTTManager
from telegram_bot import polling

mqtt_manager = MQTTManager()

class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast(self, data: dict):
        msg  = json.dumps(data, default=str)
        dead = []
        for ws in self.active:
            try:
                await ws.send_text(msg)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

ws_manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    task_mqtt     = asyncio.create_task(mqtt_manager.start(ws_manager))
    task_telegram = asyncio.create_task(polling())
    yield
    task_mqtt.cancel()
    task_telegram.cancel()
    try:
        await task_mqtt
        await task_telegram
    except asyncio.CancelledError:
        pass

app = FastAPI(
    title="Monitor IoT Posta Médica",
    description="UNMSM FISI 2026 — Consultorio General",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═══════════════════════════════════════════════════════════════
#  WEBSOCKET
# ═══════════════════════════════════════════════════════════════
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        db = SessionLocal()
        try:
            ultimo_suero    = db.query(Suero).order_by(Suero.id.desc()).first()
            ultimos_vitales = db.query(Vitales).order_by(Vitales.id.desc()).first()

            if ultimo_suero:
                await websocket.send_text(json.dumps({
                    "type": "lectura",
                    "data": ultimo_suero.to_dict(),
                    "estado": {
                        **ultimo_suero.to_dict(),
                        **(ultimos_vitales.to_dict() if ultimos_vitales else {"fc": 0, "spo2": 0, "estado_vitales": "MIDIENDO"}),
                    }
                }, default=str))

            if ultimos_vitales:
                await websocket.send_text(json.dumps({
                    "type": "vitales",
                    "data": ultimos_vitales.to_dict(),
                }, default=str))
        finally:
            db.close()

        while True:
            await asyncio.sleep(30)
            await websocket.send_text(json.dumps({"type": "ping"}))

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)

# ═══════════════════════════════════════════════════════════════
#  REST — GENERAL
# ═══════════════════════════════════════════════════════════════
@app.get("/")
def root():
    return {"status": "ok", "service": "Monitor IoT Posta Médica — UNMSM FISI 2026"}

# ═══════════════════════════════════════════════════════════════
#  REST — SUERO
# ═══════════════════════════════════════════════════════════════
@app.get("/suero")
def get_suero(limit: int = 60):
    db = SessionLocal()
    try:
        rows = db.query(Suero).order_by(Suero.id.desc()).limit(limit).all()
        return [r.to_dict() for r in reversed(rows)]
    finally:
        db.close()

@app.get("/suero/ultimo")
def get_ultimo_suero():
    db = SessionLocal()
    try:
        row = db.query(Suero).order_by(Suero.id.desc()).first()
        if not row:
            raise HTTPException(status_code=404, detail="Sin lecturas de suero aún")
        return row.to_dict()
    finally:
        db.close()

@app.get("/suero/rango")
def get_suero_rango(desde: str, hasta: str):
    db = SessionLocal()
    try:
        rows = (
            db.query(Suero)
            .filter(Suero.timestamp >= desde, Suero.timestamp <= hasta)
            .order_by(Suero.timestamp).all()
        )
        return [r.to_dict() for r in rows]
    finally:
        db.close()

# ═══════════════════════════════════════════════════════════════
#  REST — VITALES
# ═══════════════════════════════════════════════════════════════
@app.get("/vitales")
def get_vitales(limit: int = 60):
    db = SessionLocal()
    try:
        rows = db.query(Vitales).order_by(Vitales.id.desc()).limit(limit).all()
        return [r.to_dict() for r in reversed(rows)]
    finally:
        db.close()

@app.get("/vitales/ultimo")
def get_ultimos_vitales():
    db = SessionLocal()
    try:
        row = db.query(Vitales).order_by(Vitales.id.desc()).first()
        if not row:
            raise HTTPException(status_code=404, detail="Sin lecturas de vitales aún")
        return row.to_dict()
    finally:
        db.close()

@app.get("/vitales/rango")
def get_vitales_rango(desde: str, hasta: str):
    db = SessionLocal()
    try:
        rows = (
            db.query(Vitales)
            .filter(Vitales.timestamp >= desde, Vitales.timestamp <= hasta)
            .order_by(Vitales.timestamp).all()
        )
        return [r.to_dict() for r in rows]
    finally:
        db.close()

# ═══════════════════════════════════════════════════════════════
#  REST — ALERTAS
# ═══════════════════════════════════════════════════════════════
@app.get("/alertas")
def get_alertas(limit: int = 20, solo_activas: bool = False):
    db = SessionLocal()
    try:
        q = db.query(Alerta).order_by(Alerta.id.desc())
        if solo_activas:
            q = q.filter(Alerta.activa == True)
        return [r.to_dict() for r in q.limit(limit).all()]
    finally:
        db.close()

@app.delete("/alertas")
def limpiar_alertas():
    db = SessionLocal()
    try:
        db.query(Alerta).update({"activa": False})
        db.commit()
        return {"ok": True, "mensaje": "Alertas desactivadas"}
    finally:
        db.close()

# ═══════════════════════════════════════════════════════════════
#  REST — COMANDOS
# ═══════════════════════════════════════════════════════════════
class ComandoRequest(BaseModel):
    cmd:    str
    origen: str = "dashboard"  # dashboard | telegram | voz

COMANDOS_VALIDOS = {"bomba_on", "bomba_off", "reset", "tare"}

@app.post("/comandos")
async def enviar_comando(body: ComandoRequest):
    if body.cmd not in COMANDOS_VALIDOS:
        raise HTTPException(status_code=400, detail=f"Comando inválido. Válidos: {COMANDOS_VALIDOS}")
    
    # Guardar origen para que _guardar_suero lo use en el próximo ciclo
    mqtt_manager.ultimo_origen = body.origen
    
    await mqtt_manager.publicar_comando(body.cmd)
    return {"ok": True, "cmd": body.cmd, "timestamp": datetime.utcnow().isoformat()}

# ═══════════════════════════════════════════════════════════════
#  REST — EMAIL
# ═══════════════════════════════════════════════════════════════
class EmailRequest(BaseModel):
    destinatario: str
    payload: dict = {}
    alertas: list = []

@app.post("/enviar-email")
async def enviar_email_endpoint(body: EmailRequest):
    from email_service import enviar_email_familiar
    await enviar_email_familiar(
        payload      = body.payload,
        alertas      = body.alertas,
        destinatario = body.destinatario,
    )
    return {"ok": True, "destinatario": body.destinatario}

# ═══════════════════════════════════════════════════════════════
#  REST — LECTURA CONFIGURACIÓN Y ACTUALIZAR UMBRALES
# ═══════════════════════════════════════════════════════════════
class ConfigRequest(BaseModel):
    peso_alerta:  float
    peso_critico: float

@app.get("/config")
def get_configuracion():
    """Obtiene la configuración activa de umbrales."""
    db = SessionLocal()
    try:
        cfg = db.query(Config).order_by(Config.id.desc()).first()
        if cfg:
            return cfg.to_dict()
        return {"peso_alerta": 150.0, "peso_critico": 100.0}
    finally:
        db.close()

@app.post("/config")
async def guardar_configuracion(body: ConfigRequest):
    """Guarda nuevos umbrales y los envía al ESP32 por MQTT."""
    # Validar rangos
    if body.peso_critico >= body.peso_alerta:
        raise HTTPException(
            status_code=400,
            detail="El umbral crítico debe ser menor que el de alerta"
        )
    if body.peso_critico < 10 or body.peso_alerta > 490:
        raise HTTPException(
            status_code=400,
            detail="Umbrales fuera de rango (crítico: 10-490g, alerta: 10-490g)"
        )

    # Guardar en BD
    db = SessionLocal()
    try:
        cfg = Config(
            peso_alerta  = body.peso_alerta,
            peso_critico = body.peso_critico,
            updated_at   = datetime.utcnow() - timedelta(hours=5),
        )
        db.add(cfg)
        db.commit()
        db.refresh(cfg)
    finally:
        db.close()

    # Enviar al ESP32 por MQTT
    await mqtt_manager.publicar_config(body.peso_alerta, body.peso_critico)

    return {"ok": True, "config": cfg.to_dict()}

# ═══════════════════════════════════════════════════════════════
#  REST — STATS
# ═══════════════════════════════════════════════════════════════
@app.get("/stats")
def get_stats():
    db = SessionLocal()
    try:
        total_suero     = db.query(Suero).count()
        total_vitales   = db.query(Vitales).count()
        alertas_activas = db.query(Alerta).filter(Alerta.activa == True).count()
        ultimo_suero    = db.query(Suero).order_by(Suero.id.desc()).first()
        ultimos_vitales = db.query(Vitales).order_by(Vitales.id.desc()).first()
        return {
            "total_suero":     total_suero,
            "total_vitales":   total_vitales,
            "alertas_activas": alertas_activas,
            "ultimo_suero":    ultimo_suero.to_dict()    if ultimo_suero    else None,
            "ultimos_vitales": ultimos_vitales.to_dict() if ultimos_vitales else None,
            "clientes_ws":     len(ws_manager.active),
        }
    finally:
        db.close()

# ═══════════════════════════════════════════════════════════════
#  REST — USUARIOS (LOGIN)
# ═══════════════════════════════════════════════════════════════
class LoginRequest(BaseModel):
    usuario:  str
    password: str

@app.post("/login")
def login(body: LoginRequest):
    db = SessionLocal()
    try:
        user = db.query(Usuario).filter(
            Usuario.usuario == body.usuario,
            Usuario.password == body.password,
            Usuario.activo == True,
        ).first()
        if not user:
            raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
        return user.to_dict()
    finally:
        db.close()

# ═══════════════════════════════════════════════════════════════
#  REST — PACIENTES 
# ═══════════════════════════════════════════════════════════════

class PacienteRequest(BaseModel):
    nombre:            str
    apellido:          str
    codigo:            str
    doctor:            str = ""
    grupo_sanguineo:   str = ""
    fecha_nacimiento:  str = ""
    fecha_ingreso:     str = ""
    direccion:         str = ""
    contacto_nombre:   str = ""
    contacto_telefono: str = ""
    contacto_relacion: str = ""

@app.get("/pacientes")
def get_pacientes(solo_activos: bool = True):
    db = SessionLocal()
    try:
        q = db.query(Paciente)
        if solo_activos:
            q = q.filter(Paciente.activo == True)
        return [p.to_dict() for p in q.order_by(Paciente.id.desc()).all()]
    finally:
        db.close()

@app.get("/pacientes/{paciente_id}")
def get_paciente(paciente_id: int):
    db = SessionLocal()
    try:
        p = db.query(Paciente).filter(Paciente.id == paciente_id).first()
        if not p:
            raise HTTPException(status_code=404, detail="Paciente no encontrado")
        return p.to_dict()
    finally:
        db.close()

@app.post("/pacientes")
def crear_paciente(body: PacienteRequest):
    db = SessionLocal()
    try:
        # Verificar código único
        existe = db.query(Paciente).filter(Paciente.codigo == body.codigo).first()
        if existe:
            raise HTTPException(status_code=400, detail=f"El código {body.codigo} ya existe")
        p = Paciente(**body.dict(), created_at=datetime.utcnow())
        db.add(p)
        db.commit()
        db.refresh(p)
        return p.to_dict()
    finally:
        db.close()

@app.put("/pacientes/{paciente_id}")
def actualizar_paciente(paciente_id: int, body: PacienteRequest):
    db = SessionLocal()
    try:
        p = db.query(Paciente).filter(Paciente.id == paciente_id).first()
        if not p:
            raise HTTPException(status_code=404, detail="Paciente no encontrado")
        # Verificar código único (excluyendo el mismo)
        existe = db.query(Paciente).filter(
            Paciente.codigo == body.codigo,
            Paciente.id != paciente_id
        ).first()
        if existe:
            raise HTTPException(status_code=400, detail=f"El código {body.codigo} ya existe")
        for k, v in body.dict().items():
            setattr(p, k, v)
        db.commit()
        db.refresh(p)
        return p.to_dict()
    finally:
        db.close()

@app.delete("/pacientes/{paciente_id}")
def desactivar_paciente(paciente_id: int):
    """Soft delete — marca como inactivo."""
    db = SessionLocal()
    try:
        p = db.query(Paciente).filter(Paciente.id == paciente_id).first()
        if not p:
            raise HTTPException(status_code=404, detail="Paciente no encontrado")
        p.activo = False
        db.commit()
        return {"ok": True, "mensaje": f"Paciente {p.codigo} desactivado"}
    finally:
        db.close()

# ═══════════════════════════════════════════════════════════════
#  REST — SELECCIONAR PACIENTE ACTIVO + RESET
# ═══════════════════════════════════════════════════════════════

# Estado global: paciente actualmente en monitoreo
_paciente_activo_id: int | None = None

@app.get("/paciente-activo")
def get_paciente_activo():
    if _paciente_activo_id is None:
        return {"paciente": None}
    db = SessionLocal()
    try:
        p = db.query(Paciente).filter(Paciente.id == _paciente_activo_id).first()
        return {"paciente": p.to_dict() if p else None}
    finally:
        db.close()

class SeleccionarPacienteRequest(BaseModel):
    paciente_id: int

@app.post("/paciente-activo")
async def seleccionar_paciente(body: SeleccionarPacienteRequest):
    """
    Selecciona el paciente activo y resetea el sistema:
    1. Actualiza estado global
    2. Manda reset al ESP32 (limpia bomba/alertas)
    3. Broadcast a todos los clientes WebSocket
    4. El frontend limpia su historial local
    """
    global _paciente_activo_id
    db = SessionLocal()
    try:
        p = db.query(Paciente).filter(
            Paciente.id == body.paciente_id,
            Paciente.activo == True
        ).first()
        if not p:
            raise HTTPException(status_code=404, detail="Paciente no encontrado")

        _paciente_activo_id = p.id

        # Actualizar fecha de ingreso al día de hoy
        p.fecha_ingreso = datetime.now().strftime("%d-%m-%Y")
        db.commit()

        # 1. Reset físico del ESP32 (limpia bomba + alertas)
        await mqtt_manager.publicar_comando("reset")

        # 2. Broadcast a todos los WS — el frontend resetea su estado
        await ws_manager.broadcast({
            "type":    "paciente_activo",
            "paciente": p.to_dict(),
        })

        return {"ok": True, "paciente": p.to_dict()}
    finally:
        db.close()