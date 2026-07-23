# Sistema de Monitoreo IoT — Posta Médica

## Descripción

Sistema IoT end-to-end que conecta sensores físicos en una posta médica con un dashboard web en tiempo real. El ESP32 captura frecuencia cardíaca, saturación de oxígeno y nivel de suero IV, los publica vía MQTT, y el backend los procesa, genera alertas automáticas y los retransmite por WebSocket al frontend. El personal médico puede visualizar, controlar y recibir notificaciones desde cualquier dispositivo.

---

## Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                         HARDWARE (Consultorio)                  │
│  MAX30102 ──┐                                                   │
│  (FC/SpO2)  │── ESP32 ──► MQTT ──► HiveMQ Cloud               │
│  HX711 ─────┘   (tópicos: vitales / lecturas / comandos)       │
│  (Suero IV)      ◄── Comandos (bomba_on/off, tare, reset)      │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND — Railway (FastAPI)                   │
│  ┌───────────┐  ┌────────────┐  ┌───────────┐  ┌────────────┐ │
│  │mqtt_client│  │ REST API   │  │ WebSocket │  │  Alertas   │ │
│  │ (aiomqtt) │  │ (FastAPI)  │  │  /ws      │  │ Email+TG   │ │
│  └─────┬─────┘  └─────┬──────┘  └─────┬─────┘  └────────────┘ │
│        └──────────────┴────────────────┘                        │
│                        MySQL (Railway)                           │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                  FRONTEND — Vercel (React 19)                    │
│  Monitor │ Analítica │ Alertas │ Config │ Paciente │ Admin      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Stack Tecnológico

| Capa | Tecnología |
|------|-----------|
| **Microcontrolador** | ESP32 (Arduino/PlatformIO) |
| **Sensores** | MAX30102 (FC / SpO2), HX711 + celda de carga (suero IV) |
| **Broker MQTT** | HiveMQ Cloud (TLS 8883) |
| **Backend** | Python 3.12 · FastAPI 0.111 · SQLAlchemy 2.0 · aiomqtt 2.3 · Uvicorn |
| **Base de datos** | MySQL 8 (Railway plugin) |
| **Frontend** | React 19 · TypeScript 5 · Vite 7 · Recharts · lucide-react |
| **Notificaciones** | Resend API (email HTML+PDF) · Telegram Bot API |
| **Hosting** | Railway (backend + MySQL) · Vercel (frontend) |

---

## Tópicos MQTT

| Tópico | Dirección | Payload | Frecuencia |
|--------|-----------|---------|------------|
| `posta/consultorio/lecturas` | ESP32 → Backend | `{peso, bomba, estado}` | 1 Hz |
| `posta/consultorio/vitales` | ESP32 → Backend | `{fc, spo2, estado}` | 0.1 Hz |
| `posta/consultorio/comandos` | Backend → ESP32 | `{"cmd": "bomba_on\|off\|reset\|tare"}` | On-demand |
| `posta/consultorio/config` | Backend → ESP32 | `{peso_alerta, peso_critico}` | On-demand |

---

## Funcionalidades

### Monitoreo en Tiempo Real
- **Signos vitales**: Frecuencia cardíaca (FC) y saturación de oxígeno (SpO2) actualizados cada 10 s
- **Suero IV**: Nivel en ml por peso (celda de carga) con actualización cada segundo
- **Dashboard WebSocket**: Sin polling; actualizaciones push con ping keep-alive cada 30 s
- **Clasificación automática**: NORMAL · TAQUICARDIA · BRADICARDIA · HIPOXIA · HIPOXIA CRÍTICA

### Sistema de Alertas
Escalamiento automático que previene spam:

| Alerta | Condición | Nivel |
|--------|-----------|-------|
| `SUERO_BAJO` | < 150 ml | Advertencia |
| `SUERO_CRITICO` | < 100 ml | Crítico + activa bomba |
| `FC_ALTA` | > 100 bpm | Taquicardia |
| `FC_BAJA` | < 60 bpm | Bradicardia |
| `SPO2_BAJA` | < 95 % | Hipoxia |
| `SPO2_CRITICA` | < 90 % | Crítico |

- Intervalo mínimo de 5 s entre alertas Telegram (anti-spam)
- Registro completo con timestamp, valor y paciente en MySQL

### Control de Bomba
- Activación manual desde el dashboard o automática por umbral crítico
- Comandos registrados con origen (dashboard / telegram / automático)
- Teclado inline de Telegram para activar/desactivar la bomba en alertas de suero

### Gestión de Pacientes
- CRUD completo (crear, editar, desactivar)
- Asignación de médico tratante; los médicos solo ven sus propios pacientes
- Selección de paciente activo → reset + tare automático de la balanza
- Campos: nombre, apellido, código auto-generado, grupo sanguíneo, contacto familiar, fecha de ingreso

### Analítica Histórica
- Promedios por minuto para FC, SpO2 y nivel de suero
- Detección de tendencia del fluido (estable / recargando / descendiendo)
- Gráficas interactivas (Recharts) con rango de tiempo personalizable

### Notificaciones
- **Email**: Informe HTML + PDF firmado enviado a familiar del paciente (solo alertas clínicas FC/SpO2)
- **Telegram**: Alertas en tiempo real con botones inline; enlace directo al dashboard

### Autenticación y Roles
- Roles: `Administrador` · `Médico` · `Enfermero`
- Administrador: acceso a todos los pacientes y módulo de administración
- Médico: solo sus pacientes asignados
- Cambios de configuración protegidos con contraseña

---

## Estructura del Proyecto

```
proyecto_final/
├── backend/
│   ├── main.py            # API REST + WebSocket + lógica central
│   ├── mqtt_client.py     # Suscripción MQTT + detección de alertas
│   ├── models.py          # ORM SQLAlchemy (5 tablas)
│   ├── database.py        # Conexión MySQL + inicialización
│   ├── email_service.py   # Emails HTML + generación PDF (ReportLab)
│   ├── telegram_bot.py    # Bot polling + teclado inline
│   ├── requirements.txt
│   ├── Procfile           # Comando Railway
│   └── railway.toml
└── frontend/
    ├── src/
    │   ├── pages/
    │   │   ├── Monitor.tsx        # Dashboard signos vitales en vivo
    │   │   ├── Analytics.tsx      # Gráficas históricas
    │   │   ├── Paciente.tsx       # Detalle paciente + control bomba
    │   │   ├── Alertas.tsx        # Historial y filtros de alertas
    │   │   ├── Config.tsx         # Umbrales por paciente
    │   │   ├── Administracion.tsx # CRUD pacientes/médicos
    │   │   └── Login.tsx          # Autenticación (tema ECG)
    │   ├── components/
    │   │   ├── EscenaPaciente.tsx # SVG animado (bolsa IV + pulsación)
    │   │   ├── ArcoIndicador.tsx  # Gauge arco para FC/SpO2
    │   │   ├── BarraFluido.tsx    # Barra nivel de suero
    │   │   └── CorazonPulso.tsx   # Animación latido sincronizada a BPM
    │   ├── hooks/useLecturas.ts   # Hook WebSocket
    │   ├── services/api.ts        # Cliente HTTP centralizado
    │   └── tipos.ts               # Interfaces TypeScript
    ├── package.json
    └── vite.config.js
```

---

## API REST — Resumen de Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/login` | Autenticación |
| `GET` | `/pacientes` | Listar pacientes (filtrado por rol) |
| `POST` | `/pacientes` | Crear paciente |
| `PUT` | `/pacientes/{id}` | Actualizar paciente |
| `GET` | `/paciente-activo` | Paciente en monitoreo actual |
| `POST` | `/paciente-activo` | Seleccionar paciente (→ tare) |
| `GET` | `/suero/ultimo` | Última lectura de suero |
| `GET` | `/suero/por-minuto` | Agregados por minuto |
| `GET` | `/vitales` | Lecturas de FC/SpO2 |
| `GET` | `/alertas` | Historial de alertas |
| `POST` | `/comandos` | Enviar comando a ESP32 |
| `GET/POST` | `/config` | Leer/guardar umbrales |
| `POST` | `/enviar-email` | Enviar informe a familiar |
| `GET` | `/stats` | Estadísticas del sistema |
| `WS` | `/ws` | Stream WebSocket en tiempo real |

---

## Schema de Base de Datos

```
usuarios    → id · usuario · password · nombre · rol · activo
pacientes   → id · nombre · apellido · codigo · doctor_id → usuarios
suero       → id · timestamp · paciente_id · peso · bomba · estado_suero
vitales     → id · timestamp · paciente_id · fc · spo2 · estado_vitales
alertas     → id · timestamp · paciente_id · tipo · mensaje · valor · activa
config      → id · paciente_id (nullable) · peso_alerta · peso_critico
```

---

## Variables de Entorno

### Backend (`backend/.env`)
```env
MQTT_HOST=<hivemq-host>
MQTT_PORT=8883
MQTT_USER=<mqtt-user>
MQTT_PASS=<mqtt-password>
MQTT_CLIENT=FastAPI_Backend
DATABASE_URL=mysql+pymysql://user:pass@host:port/db
RESEND_API_KEY=<resend-key>
TELEGRAM_TOKEN=<bot-token>
TELEGRAM_CHAT_ID=<chat-id>
BACKEND_URL=https://<tu-backend>.up.railway.app
```

### Frontend (`frontend/.env`)
```env
VITE_API_URL=https://<tu-backend>.up.railway.app
```

---

## Despliegue

### Backend — Railway
```bash
# Railway detecta Python automáticamente con el Procfile
# Procfile: web: uvicorn main:app --host 0.0.0.0 --port $PORT
cd backend
# Configura las variables de entorno en el dashboard de Railway
# Agrega el plugin MySQL de Railway → inyecta DATABASE_URL automáticamente
```

### Frontend — Vercel
```bash
cd frontend
npm install
npm run build
# Despliega la carpeta dist/ en Vercel
# O conecta el repo en vercel.com → auto-deploy en push
```

---

## Desarrollo Local

```bash
# Backend
cd backend
pip install -r requirements.txt
cp .env.example .env   # completar variables
uvicorn main:app --reload --port 8000

# Frontend (en otra terminal)
cd frontend
npm install
echo "VITE_API_URL=http://localhost:8000" > .env
npm run dev
```

> Para pruebas sin hardware ESP32, puedes publicar mensajes MQTT manualmente  
> con cualquier cliente MQTT (MQTTX, mosquitto_pub) usando los tópicos descritos.

---

## Detalles Técnicos Notables

- **Zona horaria**: El backend guarda con offset UTC-5; el frontend parsea manualmente para evitar doble conversión
- **Anti-ruido HX711**: Variaciones ±3 ml se consideran ruido y no generan alertas
- **Escalamiento de alertas**: Sistema de niveles (BAJO → CRÍTICO) por tipo de alerta para evitar spam
- **UI optimista**: Los botones de bomba responden inmediatamente; revierten en error tras 3 s
- **Aislamiento multi-paciente**: Cada dato lleva `paciente_id`; el WebSocket filtra por paciente activo
- **Activación automática de bomba**: Cuando el suero llega a nivel crítico, la bomba se activa sin intervención humana

