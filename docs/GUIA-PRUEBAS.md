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
