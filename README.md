# 💰 Cash for English - Backend API

> Plataforma de aprendizaje de inglés con recompensas en tokens FORE

## 📖 Descripción

Backend del proyecto **Cash for English**, construido con Django REST Framework. Este proyecto implementa una arquitectura limpia y escalable para gestionar:

- 🎓 Cursos y lecciones de inglés
- 📝 Quizzes y evaluaciones
- 💎 Sistema de recompensas en tokens FORE
- 👥 Gestión de usuarios (estudiantes, profesores, administradores)
- 🔐 Autenticación JWT con refresh tokens

---

## 🏗️ Arquitectura

### Stack Tecnológico

- **Backend**: Django 5.0.2 + Django REST Framework 3.14
- **Base de datos**: PostgreSQL 15
- **Cache**: Redis 7
- **Autenticación**: JWT (djangorestframework-simplejwt)
- **Documentación API**: drf-spectacular (OpenAPI 3.0)
- **Containerización**: Docker + Docker Compose

### Estructura del Proyecto

```
CASH_FOR_ENGLISH_BACK/
├── cash_for_english/          # Proyecto principal
│   ├── settings/              # Configuraciones modulares
│   │   ├── __init__.py
│   │   ├── base.py            # Configuración base
│   │   ├── development.py     # Desarrollo
│   │   └── production.py      # Producción
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/                      # Aplicaciones Django (próximamente)
│   ├── users/                 # Gestión de usuarios
│   ├── courses/               # Cursos y lecciones
│   ├── quizzes/               # Evaluaciones
│   └── rewards/               # Sistema de tokens FORE
├── docker-compose.yml         # Servicios: web, db, redis
├── Dockerfile                 # Imagen del backend
├── requirements.txt           # Dependencias Python
├── Makefile                   # Comandos útiles
├── .env                       # Variables de entorno (no versionado)
└── .env.example               # Plantilla de variables

---

## 🚀 Setup Inicial

### Prerrequisitos

- Python 3.11+
- Docker & Docker Compose
- Git

### 1. Clonar el repositorio

```bash
git clone https://github.com/davidsalinasvmlyr/CASH_FOR_ENGLISH_BACK.git
cd CASH_FOR_ENGLISH_BACK
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
# Edita .env con tus valores
```

### 3. Opción A: Con Docker (Recomendado)

```bash
# Setup completo (construir, migrar, etc.)
make setup

# O paso a paso:
make build          # Construir imágenes
make up             # Levantar servicios
make migrate        # Aplicar migraciones
make createsuperuser  # Crear usuario admin
```

### 3. Opción B: Sin Docker (Desarrollo local)

```bash
# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Asegúrate de que PostgreSQL y Redis estén corriendo
# Actualiza .env con las credenciales locales

# Migraciones y superusuario
python manage.py migrate
python manage.py createsuperuser
```

---

## 🛠️ Comandos Útiles (Makefile)

```bash
make help           # Ver todos los comandos disponibles

# Docker
make up             # Levantar servicios
make down           # Detener servicios
make restart        # Reiniciar servicios
make logs           # Ver logs en tiempo real
make logs-web       # Ver solo logs del servicio web

# Django
make migrate        # Aplicar migraciones
make makemigrations # Crear migraciones
make shell          # Shell de Django
make bash           # Bash en contenedor

# Testing & Quality
make test           # Ejecutar tests
make test-coverage  # Tests con cobertura
make lint           # Linter (flake8)
make format         # Formatear código (black + isort)

# Utilidades
make clean          # Limpiar archivos generados
make reset-db       # Resetear base de datos (⚠️ elimina datos)
```

---

## 📚 API Endpoints

Una vez levantado el servidor, accede a:

- **Admin Panel**: http://localhost:8000/admin/
- **API Docs (Swagger)**: http://localhost:8000/api/docs/
- **API Redoc**: http://localhost:8000/api/redoc/

### Endpoints Principales (Próximamente)

```
/api/auth/
  POST /register/           # Registro de usuario
  POST /login/              # Login (obtener tokens)
  POST /refresh/            # Refrescar access token
  POST /logout/             # Logout (blacklist token)

/api/users/
  GET  /me/                 # Perfil del usuario actual
  PUT  /me/                 # Actualizar perfil

/api/courses/
  GET  /                    # Listar cursos
  GET  /{id}/               # Detalle de curso
  GET  /{id}/lessons/       # Lecciones del curso

/api/quizzes/
  GET  /                    # Listar quizzes
  POST /{id}/submit/        # Enviar respuestas

/api/rewards/
  GET  /wallet/             # Balance de tokens
  GET  /transactions/       # Historial
```

---

## 🔐 Autenticación JWT

### Flujo de Autenticación

1. **Registro**: `POST /api/auth/register/`
2. **Login**: `POST /api/auth/login/` → Devuelve `access` y `refresh` tokens
3. **Uso del API**: Incluir header `Authorization: Bearer <access_token>`
4. **Refresh**: Cuando `access` expire, usar `POST /api/auth/refresh/` con `refresh_token`

### Configuración JWT

- **Access Token**: 60 minutos
- **Refresh Token**: 24 horas
- **Blacklist activada**: Los tokens usados para logout se invalidan

---

## 🧪 Testing

```bash
# Con Docker
make test
make test-coverage

# Sin Docker
pytest
pytest --cov=. --cov-report=html
```

---

## 🎨 Code Style

Este proyecto sigue **PEP8** y usa herramientas de formateo automático:

```bash
make format  # Black + isort
make lint    # Flake8
```

### Configuración

- **Black**: Formato de código
- **isort**: Ordenar imports
- **Flake8**: Linter (max line length: 100)

---

## 🌍 Deployment (AWS)

### Preparación

1. Asegúrate de que todas las variables en `.env` estén configuradas para producción
2. Ajusta `ALLOWED_HOSTS`, `DEBUG=False`, `SECRET_KEY` seguro

### Opciones de Deploy

- **AWS Elastic Beanstalk**: Recomendado para simplicidad
- **AWS ECS + Fargate**: Para contenedores escalables
- **EC2 manual**: Usando Docker Compose

(Más detalles en fases futuras)

---

## 📦 Variables de Entorno

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `SECRET_KEY` | Clave secreta de Django | `your-secret-key` |
| `DEBUG` | Modo debug | `True` / `False` |
| `ALLOWED_HOSTS` | Hosts permitidos | `localhost,127.0.0.1` |
| `DB_NAME` | Nombre de la BD | `cash_for_english_db` |
| `DB_USER` | Usuario PostgreSQL | `postgres` |
| `DB_PASSWORD` | Contraseña PostgreSQL | `postgres_password` |
| `DB_HOST` | Host de la BD | `db` (Docker) / `localhost` |
| `DB_PORT` | Puerto PostgreSQL | `5432` |
| `REDIS_URL` | URL de Redis | `redis://redis:6379/0` |
| `JWT_ACCESS_TOKEN_LIFETIME` | Duración access token (min) | `60` |
| `JWT_REFRESH_TOKEN_LIFETIME` | Duración refresh token (min) | `1440` |

---

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama: `git checkout -b feature/nueva-funcionalidad`
3. Commit: `git commit -m 'Add: nueva funcionalidad'`
4. Push: `git push origin feature/nueva-funcionalidad`
5. Abre un Pull Request

---

## 📝 Fases del Desarrollo

- [x] **Fase 1**: Setup del proyecto y Docker
- [ ] **Fase 2**: Autenticación JWT y gestión de usuarios
- [ ] **Fase 3**: Modelos de cursos y lecciones
- [ ] **Fase 4**: Sistema de quizzes y evaluaciones
- [ ] **Fase 5**: Sistema de recompensas (tokens FORE)
- [ ] **Fase 6**: API RESTful completa
- [ ] **Fase 7**: Testing exhaustivo
- [ ] **Fase 8**: Deployment en AWS

---

## 📄 Licencia

Este proyecto es privado y confidencial.

---

## 👨‍💻 Autor

**David Salinas**  
[GitHub](https://github.com/davidsalinasvmlyr)