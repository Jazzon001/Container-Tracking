# Container-Tracking

Sistema web para dar **trazabilidad a los carros** (contenedores de bobinas) que circulan entre los procesos de producción de hilo de poliéster de **UTEXA**, identificar cuánto tiempo permanece cada uno en cada proceso y por qué, y mantener un **inventario en tiempo real de los carros disponibles**.

> **Código de verificación:** `LEARN-CAP-5BC13866`

---

## Contexto

UTEXA fabrica hilo de poliéster en tres procesos de producción:

- **POY**: produce hilo semiterminado, que es la materia prima de DTY.
- **DTY**: consume el POY y produce hilo terminado.
- **Twisting**: proceso de retorcido que recibe producto de DTY.

El producto se traslada en **carros**: contenedores con **24 bobinas de máximo 15 kg** cada una. Existen alrededor de **386 carros**. Cada carro cargado se notifica al ERP **NOW**, que genera un código único llamado **contenedor elemento**.

## Problema

NOW deja de mostrar el carro cuando el producto se consume en DTY y asume que el carro ya está libre. En la práctica, DTY retiene muchos carros vacíos durante mucho tiempo. Cuando POY se queda sin carros, debe buscarlos de urgencia en DTY. Si no los encuentra, las bobinas se colocan en tarimas y se rompe el flujo normal de producción.

NOW tampoco permite saber dónde está un carro vacío, desde cuándo, ni si está en mantenimiento.

## Solución propuesta

Un sistema **paralelo a NOW**, que no modifica los procesos de calidad ni de almacén, y que se compone de tres módulos.

### 1. Control de carros en tiempo real

- POY **escanea el código del contenedor elemento** al cargar un carro, y así se asocia carro ↔ contenedor elemento.
- Cuando el carro regresa vacío, **almacén lo busca en el sistema y lo marca como entregado**. Entonces pasa al inventario de carros disponibles de POY.
- POY consulta en tiempo real **cuántos carros tiene disponibles, cuáles no han regresado y desde hace cuánto tiempo**.

### 2. Mantenimiento de carros

- Registro de **fecha de entrada y de salida** de mantenimiento por carro.
- Aplica a los carros de POY y a los carros propios de DTY.

### 3. Reporte de tiempos por etapa

- Se **sube un archivo Excel descargado de NOW**.
- El sistema lo combina con los registros propios y entrega un reporte del **tiempo que cada contenedor elemento estuvo en cada proceso**, para detectar cuellos de botella.
- Etapas de NOW que se pueden cruzar: notificado → liberado por calidad → transferido a custodia → salida de custodia / entrada a DTY.

## Flujo de los carros

| Origen | Destino | Estado del carro |
|---|---|---|
| POY | DTY | Con producto |
| DTY | POY | Vacío |
| DTY | Empaque / Twisting | Con producto (carros propios de DTY) |
| Empaque / Twisting | DTY | Vacío |

## Requisitos clave

- **Captura de códigos** con lector de código de barras **y** escritura manual en el mismo campo.
- **Responsive**: debe poder usarse desde el celular.
- **Roles**: POY, Almacén, DTY, Twisting y Administrador, con permisos por rol.
- **Concurrencia**: al menos 4 usuarios simultáneos, con validaciones para que un carro no se asigne dos veces a la vez.

## Stack tecnológico

| Capa | Tecnología |
|---|---|
| Frontend | Angular |
| Backend | Python con FastAPI |
| Pruebas | Pytest (backend) y pruebas de Angular (frontend) |
| CI | GitHub Actions |

## Estructura prevista del repositorio

```
Container-Tracking/
├── backend/      # API FastAPI
├── frontend/     # Aplicación Angular
├── docs/         # Documentación y decisiones técnicas
└── .github/
    └── workflows/  # Integración continua
```

## Estado del proyecto

Backend (FastAPI + SQLAlchemy) y frontend (Angular) en desarrollo.

| Módulo | Estado |
|---|---|
| 1. Control de carros en tiempo real | Carga, entrega y consulta de carros disponibles implementadas |
| 2. Mantenimiento de carros | Entrada, salida e historial implementados |
| 3. Reporte de tiempos por etapa | Pendiente |
| Roles y autenticación | Inicio de sesión con JWT y permisos por rol implementados |
| Frontend (Angular) | Inicio de sesión, lista de carros con resumen por estado, desde hace cuánto está cada carro así y actualización automática, carga de carros (POY), recepción (Almacén) y mantenimiento (POY y DTY) con campo de escaneo |

### Endpoints disponibles

| Método y ruta | Qué hace |
|---|---|
| `POST /auth/login` | Inicia sesión y devuelve un token y el rol del usuario |
| `POST /usuarios` | Crea un usuario (solo administrador) |
| `POST /carros` | Registra un carro (número y tipo: `poy`, `dty` o `twisting`) |
| `GET /carros` | Lista carros; filtros opcionales `?estado=`, `?numero=` y `?tipo=` |
| `GET /carros/{id}` | Consulta un carro |
| `POST /carros/{id}/carga` | POY carga un carro con su contenedor elemento |
| `POST /carros/{id}/entrega` | Almacén recibe el carro vacío |
| `POST /carros/{id}/mantenimiento` | Un carro disponible entra a mantenimiento |
| `POST /carros/{id}/mantenimiento/salida` | El carro sale de mantenimiento |
| `GET /carros/{id}/mantenimiento` | Historial de mantenimiento del carro |

Con el servidor en marcha, la documentación interactiva está en `/docs`.

### Carga inicial de carros

Los carros se importan del Excel que se descarga de NOW (hoja `Containers`; el tipo de producto `C01`, `C02` y `C03` corresponde a carros de POY, DTY y Twisting). Desde `backend`: `python -m scripts.importar_carros <archivo.xlsx>` revisa sin guardar y, con `--guardar`, agrega los carros nuevos como disponibles; repetirlo no duplica. Los archivos con datos reales van en `datos/`, que no se sube a GitHub.

### Permisos por rol

Todas las rutas, salvo `/health` y `/auth/login`, exigen iniciar sesión. El administrador puede realizar cualquier operación.

| Operación | Roles permitidos (además del administrador) |
|---|---|
| Consultar carros y su historial de mantenimiento | Todos |
| Registrar un carro, crear usuarios | Solo administrador |
| Cargar un carro | POY |
| Recibir un carro vacío (entrega) | Almacén |
| Registrar entrada y salida de mantenimiento | POY y DTY |

### Documentación

- [Guía de pruebas y flujo de trabajo](docs/GUIA-PRUEBAS.md): cómo instalar, ejecutar y probar.
- [Arquitectura (C4)](docs/arquitectura.md) y [decisiones (ADR)](docs/adr/).
- [Modelo de datos en JSON](docs/modelo-de-datos.json), generado con `python -m scripts.exportar_modelo` desde `backend/`.

## Convenciones de trabajo

- Commits con el formato **Conventional Commits** (`feat:`, `fix:`, `docs:`, `test:`, `chore:`).
- Un commit por cambio lógico, trabajando en ramas por funcionalidad.
- Las pruebas y el CI deben pasar antes de integrar cambios.

## Cliente

- **Empresa:** UTEXA
- **Cliente directo:** William Castillo, ingeniero del sistema de gestión de calidad
- **ERP de referencia:** NOW
