# Reglas de trabajo para Claude

## Git
- **No hacer `git commit` ni `git push`** (ni `git add`, `git merge`, etc. que preparen una subida). Eso lo hace siempre el dueño del proyecto, para decidir qué sube y qué no.
- Claude puede crear y editar archivos, y ejecutar comandos de solo lectura (`git status`, `git diff`, `git log`).
- Si el dueño tiene dudas con Git, Claude explica y da los comandos exactos, pero no los ejecuta por él.
- Al terminar un cambio, Claude indica qué archivos se modificaron y sugiere el mensaje de commit (Conventional Commits).
