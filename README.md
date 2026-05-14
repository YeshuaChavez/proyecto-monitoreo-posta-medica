# 🏥 Sistema de Monitoreo — Posta Médica

> Plataforma web full-stack para el monitoreo en tiempo real de indicadores de atención en postas médicas. Desarrollada con **TypeScript + React** en el frontend y **Python** en el backend, con despliegue en la nube.

---

## Descripción

Este sistema permite registrar, visualizar y hacer seguimiento de métricas clave de atención médica en postas de salud, facilitando la toma de decisiones del personal administrativo y de salud. La plataforma centraliza información de pacientes, tiempos de espera, consultas y otros indicadores operativos en un dashboard interactivo.

---

## Funcionalidades principales

- **Dashboard de indicadores** — Visualización en tiempo real de métricas de atención
- **Registro de pacientes** — Gestión de datos de entrada y consultas
- **Monitoreo de tiempos** — Seguimiento de tiempos de espera y atención
- **Historial de atenciones** — Consulta y filtrado de registros anteriores
- **Autenticación de usuarios** — Control de acceso por roles
- **Diseño responsivo** — Adaptado para uso en escritorio y móvil

---

## 🛠️ Stack Tecnológico

### Frontend
| Tecnología | Uso |
|---|---|
| TypeScript | Lenguaje principal |
| React | Framework UI |
| Vite | Bundler y entorno de desarrollo |
| Vercel | Despliegue y hosting |

### Backend
| Tecnología | Uso |
|---|---|
| Python | Lenguaje principal |
| FastAPI / Flask | API REST |
| SQLite / PostgreSQL | Base de datos |

---

## Estructura del Proyecto

```
proyecto-monitoreo-posta-medica/
│
├── frontend/                  # Aplicación React + TypeScript
│   ├── src/
│   │   ├── components/        # Componentes reutilizables
│   │   ├── pages/             # Vistas principales
│   │   ├── services/          # Llamadas a la API
│   │   └── types/             # Tipos TypeScript
│   └── package.json
│
├── backend/                   # API REST en Python
│   ├── app/
│   │   ├── routes/            # Endpoints de la API
│   │   ├── models/            # Modelos de datos
│   │   └── services/          # Lógica de negocio
│   └── requirements.txt
│
└── README.md
```

---

## Instalación y Uso Local

### Requisitos previos
- Node.js 18+
- Python 3.10+
- npm o yarn

### 1. Clonar el repositorio

```bash
git clone https://github.com/YeshuaChavez/proyecto-monitoreo-posta-medica.git
cd proyecto-monitoreo-posta-medica
```

### 2. Configurar el Backend

```bash
cd backend
pip install -r requirements.txt
python main.py
```

> La API estará disponible en `http://localhost:8000`

### 3. Configurar el Frontend

```bash
cd frontend
npm install
npm run dev
```

> La app estará disponible en `http://localhost:5173`

---

## Despliegue

El frontend está desplegado en **Vercel** con CI/CD automático desde la rama `main`.

El backend puede desplegarse en **Railway**, **Render** o cualquier plataforma compatible con Python.

---

## Equipo de Desarrollo

| Desarrollador | GitHub |
|---|---|
| **Yeshua Chavez** | [@YeshuaChavez](https://github.com/YeshuaChavez) |
| **Sebastián Fuentes Poma** | [@sebastianfuentesp-ship-it](https://github.com/sebastianfuentesp-ship-it) |

---

## Licencia

Este proyecto fue desarrollado con fines académicos y de portafolio.

---

<div align="center">
  <sub>Hecho con ❤️ en Perú 🇵🇪</sub>
</div>
