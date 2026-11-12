# Guía de trabajo y pruebas (paso a paso)

Pensada para quien nunca ha trabajado con pruebas automáticas, CI ni Git por ramas. Todos los comandos son para **PowerShell** en Windows.

## 1. Conceptos básicos

- **Prueba automática (test):** un pequeño programa que usa tu código y comprueba que responde lo esperado. Si algo se rompe, la prueba falla y te avisa antes de que llegue a producción.
- **pytest:** la herramienta que busca y ejecuta las pruebas del backend.
- **Entorno virtual (`.venv`):** una carpeta con las librerías de Python solo de este proyecto, para no mezclarlas con las de tu computadora. No se sube a Git.
- **CI (GitHub Actions):** un servidor de GitHub que, cada vez que haces `push`, instala el proyecto desde cero y corre las pruebas. Si pasan, aparece una ✅ junto al commit; si no, una ❌.
- **Base de datos de pruebas:** las pruebas usan SQLite **en memoria**, nueva y vacía en cada prueba. Nunca tocan tus datos reales ni Supabase.

## 2. Preparar el entorno (solo la primera vez)

Desde la carpeta `backend`:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Sabes que el entorno está activo porque el prompt empieza con `(.venv)`.

> Si PowerShell bloquea el script de activación, ejecuta una vez:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` y vuelve a intentarlo.

Cada vez que abras una terminal nueva, solo repite la línea de `Activate.ps1`.

## 3. Correr las pruebas

Con el entorno activo, dentro de `backend`:

```powershell
pytest
```

Más detalle (nombre de cada prueba):

```powershell
pytest -v
```

Solo un archivo, o solo una prueba:

```powershell
pytest test/test_carros.py
pytest test/test_carros.py::test_listar_carros
```

### Cómo leer el resultado

- `9 passed` en verde: todo bien.
- `FAILED` o `ERROR` en rojo: algo falla. Más abajo pytest muestra **qué línea** falló y **qué esperaba contra qué obtuvo** (`assert 409 == 201`, por ejemplo). Empieza leyendo de ahí.
- Los avisos amarillos (`warnings`) no son errores.

## 4. Probar la API a mano

Arranca el servidor (con el entorno activo, dentro de `backend`):

```powershell
uvicorn app.main:app --reload
```

Abre en el navegador **http://127.0.0.1:8000/docs**. Es una página interactiva donde puedes probar cada endpoint con el botón *Try it out*. Para detener el servidor: `Ctrl + C`.

Al arrancar crea un archivo `container_tracking.db` (SQLite local con tus datos de desarrollo). Está en `.gitignore`; si lo borras, se vuelve a crear vacío.

## 5. Base de datos: local y producción

La API lee la variable de entorno `DATABASE_URL`:

| Entorno | Valor |
|---|---|
| Local (por defecto) | No definas nada: usa `sqlite:///./container_tracking.db` |
| Pruebas | Las pruebas se encargan solas (SQLite en memoria) |
| Producción | La cadena de conexión de Supabase (PostgreSQL), definida **solo** como variable de entorno en Render |

**Nunca escribas la cadena de Supabase en un archivo del repositorio.** Contiene la contraseña y el checker de la universidad revisa que no haya secretos.

### Migraciones: cómo cambiar el modelo de datos sin perder datos

El esquema de la base (tablas y columnas) se versiona con **migraciones** (Alembic), en `backend/migrations/versions/`. Cada migración es un archivo que dice cómo pasar de una versión de la base a la siguiente, así los cambios llegan igual a tu computadora y a Supabase **sin borrar nada**.

- **La API aplica las migraciones sola al arrancar**, y los scripts (`crear_usuario`, `importar_carros`) también. No tienes que correr nada aparte.
- **Si cambias un modelo** (por ejemplo, agregas una columna en `app/models.py`), crea su migración desde `backend`, con el entorno activo:

  ```powershell
  alembic revision --autogenerate -m "agregar columna observaciones a carros"
  ```

  Revisa el archivo nuevo en `migrations/versions/`: Alembic lo escribe comparando tus modelos con la base, pero conviene leerlo antes de subirlo. Se incluye en el commit junto con el cambio del modelo.
- **Si olvidas la migración**, la prueba `test_el_esquema_de_las_migraciones_coincide_con_los_modelos` falla y te lo dice.
- Comandos útiles: `alembic current` (qué versión tiene tu base), `alembic history` (todas las versiones) y `alembic downgrade -1` (deshace la última).

> **Una sola vez:** si tu `container_tracking.db` es de antes de que existieran las migraciones, bórrala (con la API apagada) y vuelve a crear tu usuario y los carros: `Remove-Item container_tracking.db`. Desde ahí, las migraciones se encargan.

## 5.1 Seguridad: clave del token y primer administrador

La API firma los tokens de inicio de sesión con una clave secreta que se lee de la variable de entorno `JWT_SECRET`. **Las pruebas la definen solas**, pero para arrancar el servidor tú debes definirla (cada vez que abras una terminal nueva):

```powershell
$env:JWT_SECRET = "escribe-aqui-un-texto-largo-y-aleatorio"
```

Si prefieres generar una clave aleatoria:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Nunca guardes esta clave en un archivo del proyecto ni la subas a GitHub.** En producción se define solo como variable de entorno en Render.

Como crear usuarios exige ser administrador, el primero se crea desde la terminal (con el entorno activo, dentro de `backend`):

```powershell
python -m scripts.crear_usuario admin admin
```

El script te pide la contraseña por teclado (no se muestra al escribir). Después, para probar en el navegador:

1. Arranca el servidor y abre **http://127.0.0.1:8000/docs**.
2. En `POST /auth/login`, usa *Try it out* con tu usuario y contraseña. Copia el `access_token` de la respuesta.
3. Pulsa el botón **Authorize** (arriba a la derecha), pega el token y acepta.
4. Ya puedes probar el resto de los endpoints con esa sesión.

Si ves **401**, no has iniciado sesión o el token venció. Si ves **403**, tu usuario no tiene el rol que esa operación exige.

### Medir la cobertura de las pruebas

La cobertura indica qué porcentaje del código ejecutan las pruebas. Instala las herramientas de desarrollo (una vez) y corre:

```powershell
pip install -r requirements-dev.txt
pytest --cov=app --cov-report=term-missing
```

La columna `Missing` lista las líneas que ninguna prueba toca.

## 5.2 Frontend (Angular)

Requiere **Node.js** (el proyecto se probó con Node 24). Desde la carpeta `frontend`:

```powershell
cd frontend
npm install
npm start
```

Abre **http://localhost:4200**. El frontend habla con la API en `http://127.0.0.1:8000`, así que el backend debe estar corriendo en **otra terminal** (con `JWT_SECRET` definida, como en la sección 5.1) y con un usuario creado.

Si el navegador muestra un error de **CORS**, la API no está permitiendo el origen del frontend. Por defecto acepta `http://localhost:4200` y `http://127.0.0.1:4200`; para otros dominios (por ejemplo, el de Vercel) se define la variable de entorno `CORS_ORIGINS`, separada por comas.

Pruebas y compilación:

```powershell
npx ng test --no-watch
npm run build
```

La primera línea ejecuta las pruebas una sola vez (sin `--no-watch` se quedan esperando cambios; sal con `Ctrl + C`).

> **Ojo con OneDrive:** tu carpeta del proyecto está dentro de OneDrive, y `node_modules` contiene decenas de miles de archivos que OneDrive intentará sincronizar (lento, y a veces con conflictos). Lo más cómodo es mover el repositorio fuera de OneDrive (por ejemplo, a `C:\dev\Container-Tracking`) o pausar la sincronización mientras trabajas.

## 5.3 Encender todo desde VS Code

El proyecto trae tareas de VS Code (`.vscode/tasks.json`) para no escribir comandos a mano. Abre la **carpeta raíz del repositorio** en VS Code (`Container-Tracking`, no `backend` ni `frontend`).

**Preparación (solo la primera vez)**

1. Crea tu archivo de clave local: copia `backend/.env.example` como `backend/.env` y escribe en `JWT_SECRET=` un texto largo y aleatorio (el propio archivo de ejemplo indica cómo generarlo). El `.env` está en `.gitignore`: nunca se sube a GitHub.
2. Instala las dependencias: `Ctrl + Shift + P` → **Tasks: Run Task** → **Instalar dependencias (todo)**.
3. Crea tu usuario administrador: **Tasks: Run Task** → **Crear usuario**. Te pide el nombre y el rol, y luego la contraseña en la terminal.

**Cada día**

- **`Ctrl + Shift + B`** (o *Tasks: Run Task* → **Iniciar todo**) enciende la API (`http://127.0.0.1:8000`) y el frontend (`http://localhost:4200`) a la vez, cada uno en su propia terminal.
- **Todas las pruebas:** *Tasks: Run Task* → **Todas las pruebas** (o las del backend y las del frontend por separado).
- Para **apagar** un servidor, entra a su terminal y pulsa `Ctrl + C` (o cierra el panel de esa terminal).

**Otras tareas disponibles**

| Tarea | Para qué sirve |
|---|---|
| API (backend) | Solo la API, con recarga automática al guardar |
| Frontend (Angular) | Solo la interfaz |
| Pruebas del backend | pytest con cobertura |
| Pruebas del frontend | Pruebas de Angular, una sola vez |
| Crear usuario | Alta de usuarios de cualquier rol |

**Notas**

- Las tareas usan el entorno virtual de `backend/.venv`, así que **no hace falta activarlo** a mano.
- Con la extensión **Python** de Microsoft, el panel *Testing* (matraz) de VS Code también descubre las pruebas del backend.
- Si cambiaste de computadora o borraste `backend/.venv`, vuelve a crearlo como en la sección 2.
- Las rutas de las tareas son de **Windows** (`.venv\Scripts\python.exe`).

## 5.4 Importar los carros desde el Excel de NOW

El Excel (hoja `Containers`, con las columnas `IT` y `Code`) se deja en la carpeta `datos/` de la raíz del proyecto. Esa carpeta está en `.gitignore`: son datos reales de la empresa y **nunca deben subirse a GitHub**.

Los tipos de producto de NOW son: `C01` = carros de POY, `C02` = carros de DTY y `C03` = carros de Twisting.

Desde `backend`, con el entorno activo (y las dependencias al día: `pip install -r requirements-dev.txt`):

```powershell
python -m scripts.importar_carros ..\datos\Carros.xlsx
```

Sin `--guardar` **no escribe nada**: muestra cuántos carros nuevos habría por tipo, cuántos ya existen y las filas con problemas (con su número de fila). Si todo se ve bien:

```powershell
python -m scripts.importar_carros ..\datos\Carros.xlsx --guardar
```

- Todos los carros quedan **disponibles**.
- Se puede repetir sin miedo: los carros que ya existen se omiten y no se modifican.
- Si la base local es de antes de que existiera el tipo de carro, bórrala y vuelve a crear tu usuario (ver la sección 5).
- Para cargarlos en producción (Supabase), el mismo comando se ejecuta con `DATABASE_URL` apuntando a esa base. Esa cadena es secreta: defínela solo en tu terminal, nunca en un archivo del proyecto.

## 6. Flujo de trabajo diario con Git

Un cambio pequeño y completo por vez:

1. Escribe o modifica código.
2. Escribe o ajusta la prueba que lo cubre.
3. Corre `pytest` y confirma que todo pasa.
4. Revisa qué cambió:

   ```powershell
   git status
   git diff
   ```

5. Agrega **solo los archivos de ese cambio** y haz el commit:

   ```powershell
   git add backend/app backend/test
   git commit -m "feat: descripción corta de lo que hiciste"
   ```

6. Sube los cambios y revisa la pestaña **Actions** de GitHub:

   ```powershell
   git push origin main
   ```

Después de cada `git add`, usa `git status` y confirma que lo preparado es lo que querías. Una carpeta sin agregar (como pasó con `backend/app/`) hace que el CI falle aunque en tu máquina funcione.

### Prefijos de commit (Conventional Commits)

| Prefijo | Cuándo usarlo |
|---|---|
| `feat:` | Funcionalidad nueva |
| `fix:` | Corrección de un error |
| `test:` | Solo pruebas |
| `docs:` | Solo documentación |
| `chore:` | Configuración, CI, mantenimiento |

## 7. Qué hacer cuando el CI falla (❌)

1. En GitHub abre la pestaña **Actions** y entra a la corrida con ❌.
2. Abre el paso que falló y lee las últimas líneas del log.
3. Intenta reproducirlo en tu máquina con `pytest`.
4. Si no entiendes el error, copia las últimas 20–30 líneas del log y pídele ayuda a Claude.

Causas frecuentes: un archivo que no se agregó al commit, una dependencia que falta en `requirements.txt`, o una prueba que depende de datos locales.

## 8. Reglas de oro

- Si cambias el comportamiento de la API, cambia o agrega su prueba.
- No subas `.env`, contraseñas, llaves ni archivos `.db`.
- Corre `pytest` antes de cada commit.
- No fuerces el push ni reescribas la historia ya subida.
