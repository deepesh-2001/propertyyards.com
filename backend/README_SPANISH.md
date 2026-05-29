# PropertyYards Backend

Servicio backend basado en FastAPI para la plataforma inmobiliaria PropertyYards con características completas que incluyen gestión de propiedades, autenticación de usuarios, sistema de recompensas y almacenamiento en caché avanzado.

## 🚀 Características

### Funcionalidad Principal
- **Gestión de Propiedades**: Operaciones CRUD de propiedades con búsqueda y filtrado avanzados
- **Autenticación de Usuarios**: Autenticación basada en JWT con control de acceso basado en roles
- **Procesamiento de Pagos**: Integración de pagos seguros con múltiples proveedores
- **Sistema de Recompensas**: Sistema integral de puntos y comisiones con opciones de conversión
- **Análisis**: Capacidades de análisis e informes en tiempo real
- **Integración IA**: Recomendaciones de propiedades impulsadas por IA y optimización SEO

### Características Avanzadas
- **Seguridad**: Detección avanzada de amenazas, limitación de velocidad y saneamiento de entrada
- **Almacenamiento en Caché**: Almacenamiento en caché multicapa basado en Redis con invalidación inteligente
- **Monitoreo**: Monitoreo de rendimiento y verificaciones de salud
- **Documentación API**: Documentación OpenAPI/Swagger generada automáticamente

## 🛠️ Stack Tecnológico

- **Framework**: FastAPI 0.104.1
- **Base de Datos**: MongoDB con Motor (controlador async)
- **Caché**: Redis con aioredis
- **Autenticación**: JWT con python-jose
- **Seguridad**: bcrypt, slowapi para limitación de velocidad
- **Pruebas**: pytest con soporte async
- **Documentación**: OpenAPI/Swagger

## 🚀 Inicio Rápido

### Prerrequisitos
- Python 3.8+
- MongoDB
- Redis
- Git

### Instalación

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/your-org/propertyyards-backend.git
   cd propertyyards-backend
   ```

2. **Crear entorno virtual**
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno**
   ```bash
   cp .env.example .env
   # Editar .env con tu configuración
   ```

5. **Iniciar servicios**
   ```bash
   # Iniciar MongoDB y Redis (usando Docker)
   docker-compose up -d mongodb redis

   # Ejecutar la aplicación
   python run.py
   ```

### Configuración Docker

```bash
# Construir y ejecutar con Docker
docker-compose up -d

# Ver registros
docker-compose logs -f backend
```

## ⚙️ Configuración

### Variables de Entorno

```bash
# Base de Datos
MONGODB_URL=mongodb://localhost:27017/housing_db
MONGO_ROOT_PASSWORD=your_password

# Redis
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=3600

# JWT
JWT_SECRET_KEY=your_secret_key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Aplicación
DEBUG=False
SECRET_KEY=your_app_secret
API_V1_STR=/api/v1
```

## 📚 Documentación API

Una vez que el servidor está en ejecución, visita:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 📁 Estructura del Proyecto

```
backend/
├── app/                    # Código de la aplicación
│   ├── api/               # Rutas API
│   ├── auth.py            # Lógica de autenticación
│   ├── cache.py           # Capa de caché
│   ├── config.py          # Configuración
│   ├── database.py        # Conexión a base de datos
│   ├── models.py          # Modelos de datos
│   ├── security.py        # Middleware de seguridad
│   └── services/          # Lógica de negocio
├── tests/                 # Suite de pruebas
├── scripts/               # Scripts de utilidad
├── requirements.txt       # Dependencias Python
├── pyproject.toml         # Configuración del proyecto
├── Dockerfile             # Configuración Docker
├── docker-compose.yml     # Servicios de desarrollo
└── README.md              # Este archivo
```

## 🧪 Desarrollo

### Ejecutar Pruebas

```bash
# Ejecutar todas las pruebas
pytest

# Ejecutar con cobertura
pytest --cov=app

# Ejecutar archivo de prueba específico
pytest tests/test_auth.py
```

### Calidad de Código

```bash
# Formatear código
black app/ tests/

# Analizar código
flake8 app/ tests/

# Verificación de tipos
mypy app/
```

### Migraciones de Base de Datos

```bash
# Inicializar base de datos
python -m app.init_db

# Crear índices
python -m app.create_indexes
```

## 🔌 Endpoints API

### Autenticación
- `POST /api/auth/login` - Inicio de sesión de usuario
- `POST /api/auth/register` - Registro de usuario
- `POST /api/auth/refresh` - Token de actualización
- `POST /api/auth/logout` - Cierre de sesión de usuario

### Propiedades
- `GET /api/properties` - Listar propiedades
- `POST /api/properties` - Crear propiedad
- `GET /api/properties/{id}` - Obtener propiedad
- `PUT /api/properties/{id}` - Actualizar propiedad
- `DELETE /api/properties/{id}` - Eliminar propiedad

### Recompensas
- `GET /api/rewards/wallet` - Obtener billetera de recompensas
- `POST /api/rewards/convert-points` - Convertir puntos a efectivo
- `GET /api/rewards/conversion/history` - Historial de conversiones
- `GET /api/rewards/referral/code` - Obtener código de referido

### Administración
- `GET /api/admin/stats` - Estadísticas del sistema
- `POST /api/admin/process-commission` - Procesar comisión
- `GET /api/admin/users` - Gestión de usuarios

## 🔒 Características de Seguridad

### Detección de Amenazas
- Protección contra inyección SQL
- Detección de ataques XSS
- Prevención de recorrido de ruta
- Limitación de velocidad por endpoint
- Bloqueo de IP para actividad sospechosa

### Autenticación y Autorización
- Autenticación basada en token JWT
- Control de acceso basado en roles (RBAC)
- Gestión de sesiones
- Soporte de autenticación multifactor

### Protección de Datos
- Saneamiento y validación de entrada
- Hashing de contraseñas con bcrypt
- Configuración CORS
- Middleware de encabezados de seguridad

## 🚀 Estrategia de Almacenamiento en Caché

### Almacenamiento en Caché Multicapa
- **L1**: Almacenamiento en caché a nivel de aplicación
- **L2**: Almacenamiento en caché distribuido Redis
- **L3**: Almacenamiento en caché de consultas de base de datos

### Características de Caché
- Invalidación inteligente
- Calentamiento de caché para datos accedidos frecuentemente
- Monitoreo de rendimiento y métricas
- Mecanismos de respaldo para fallas de caché

## 📊 Monitoreo y Registro

### Verificaciones de Salud
- `/health` - Verificación de salud básica
- `/health/detailed` - Salud detallada del sistema
- `/metrics` - Métricas de la aplicación

### Registro
- Registro estructurado JSON
- Registro de solicitud/respuesta
- Seguimiento de errores y alertas
- Monitoreo de rendimiento

## 🚀 Despliegue

### Despliegue de Producción

```bash
# Construir imagen de producción
docker build -t propertyyards-backend .

# Ejecutar con configuración de producción
docker run -d --name backend \
  -e MONGODB_URL=mongodb://mongo:27017/housing_db \
  -e REDIS_URL=redis://redis:6379/0 \
  -p 8000:8000 \
  propertyyards-backend
```

### Configuraciones Específicas de Entorno

- **Desarrollo**: Modo depuración, bases de datos locales
- **Puesta en Escena**: Configuración similar a producción con datos de prueba
- **Producción**: Configuración optimizada, monitoreo habilitado

## 🎯 Optimización de Rendimiento

### Optimización de Base de Datos
- Estrategia de indexación MongoDB
- Agrupación de conexiones
- Optimización de consultas
- Políticas de archivado de datos

### Optimización API
- Compresión de respuesta
- Paginación para conjuntos de datos grandes
- Estrategias de almacenamiento en caché
- Patrones async/await

### Gestión de Memoria
- Reutilización de conexiones
- Perfilado de memoria
- Optimización de recolección de basura
- Limpieza de recursos

## 🤝 Contribución

1. Bifurcar el repositorio
2. Crear rama de característica (`git checkout -b feature/amazing-feature`)
3. Confirmar cambios (`git commit -m 'Add amazing feature'`)
4. Empujar a la rama (`git push origin feature/amazing-feature`)
5. Abrir Solicitud de Extracción

## 📄 Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## 📞 Soporte

- **Documentación**: [Documentación API](http://localhost:8000/docs)
- **Problemas**: [Problemas de GitHub](https://github.com/your-org/propertyyards-backend/issues)
- **Discusiones**: [Discusiones de GitHub](https://github.com/your-org/propertyyards-backend/discussions)

## 🔗 Repositorios Relacionados

- [Repositorio Frontend](https://github.com/your-org/propertyyards-frontend)
- [Repositorio Infraestructura](https://github.com/your-org/propertyyards-infrastructure)
- [Repositorio Documentación](https://github.com/your-org/propertyyards-docs)
