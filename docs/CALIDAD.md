# Calidad de código: cobertura y SonarCloud

## Qué se mide

| Qué | Cómo | Dónde se ve |
|---|---|---|
| **Cobertura de líneas** | pytest (backend) y Vitest (frontend) | `coverage/lcov.info` y `coverage/coverage-summary.json`, en la raíz del repositorio |
| **Calidad del código** | SonarCloud: bugs, vulnerabilidades, *code smells*, duplicación y *quality gate* | El panel público del proyecto en sonarcloud.io |

El CI **falla si la cobertura baja del 80 %** (backend y frontend).

## Generar el reporte de cobertura

Desde la carpeta `backend`, con el entorno virtual activo y las dependencias del frontend instaladas (`npm install` en `frontend`):

```powershell
python -m scripts.generar_cobertura
```

Corre las pruebas de los dos lados con cobertura y escribe los reportes unificados en `coverage/`. Después se suben a GitHub (`git add coverage`, commit y push). **Hay que regenerarlos y subirlos cuando cambie el código**: el número que declares en el formulario del curso debe coincidir con el archivo del repositorio.

`coverage-summary.json` usa el formato de Istanbul (`total.lines.pct`). En ese formato las *statements* se miden con las mismas líneas, porque lcov no distingue entre ambas.

## SonarCloud: pasos que solo puedes hacer tú

El código ya está preparado (`sonar-project.properties` y el trabajo `sonar` del CI). Falta crear el proyecto en tu cuenta y dar el token, que es un secreto.

1. Entra a [sonarcloud.io](https://sonarcloud.io) con **Log in → GitHub**.
2. **Importa tu cuenta personal de GitHub como organización** (plan **Free**, que es el de los proyectos públicos).
3. **Analiza un proyecto nuevo** y elige el repositorio `Container-Tracking`.
4. Cuando pregunte cómo analizar, elige **"With GitHub Actions"** (análisis desde el CI). **No uses el análisis automático**: no admite cobertura, y el *quality gate* fallaría. Si quedó activado, desactívalo en *Administration → Analysis Method*.
5. SonarCloud te muestra un **token**. Cópialo y guárdalo **solo** como secreto de GitHub: en tu repositorio, *Settings → Secrets and variables → Actions → New repository secret*, con el nombre exacto `SONAR_TOKEN`. **Nunca lo pegues en el repositorio ni en una conversación.**
6. Anota la **clave de la organización** (*Organization key*) y la **clave del proyecto** (*Project key*). No son secretas. Escríbelas en las dos líneas marcadas de `sonar-project.properties`.
7. Confirma que el proyecto es **público**: *Administration → Visibility → Public*.
8. Sube los cambios. El CI corre el trabajo `sonar` y el panel se llena en unos minutos.

## Qué exige el verificador del curso

Lee la API pública de SonarCloud en vivo:

| Indicador | Umbral |
|---|---|
| Quality gate | OK |
| Bugs y vulnerabilidades | 0 |
| Code smells | ≤ 50 |
| Duplicación | ≤ 5 % |
| Líneas analizadas | ≥ 400 |

El *quality gate* por defecto ("Sonar way") exige, entre otras cosas, que los *security hotspots* estén revisados al 100 %. Si aparecen, hay que abrirlos en SonarCloud y marcarlos como revisados (seguros) con una justificación, o corregir el código.

## Corregir un code smell (para el formulario)

El formulario pide el SHA de **un commit donde corrijas un code smell** de verdad, y qué hiciste. El proceso honesto:

1. En SonarCloud, abre **Issues** y filtra por tipo *Code Smell*.
2. Elige uno que entiendas, lee **por qué** Sonar lo marca (cada uno trae su regla y una explicación) y corrígelo en el código.
3. Haz un commit **solo** de esa corrección, con un mensaje que nombre la regla.
4. Obtén el SHA corto con `git log -1 --format=%h`.
5. Explica en tu respuesta: qué regla era, por qué Sonar la marcaba y qué cambiaste.
