# Tablero de Rutas — Albion Online (Flask + Supabase + Render)

## 1. Supabase

1. Crea un proyecto nuevo en Supabase (o usa uno existente).
2. Ve a **SQL Editor** y corre todo el contenido de `schema.sql`.
3. Ve a **Project Settings → API** y copia:
   - `Project URL` → variable `SUPABASE_URL`
   - `service_role key` (no la `anon key`, porque el backend necesita permisos de escritura) → variable `SUPABASE_KEY`

## 2. Subir a GitHub

Igual que tus otros proyectos: crea el repo, sube estos archivos con push directo.

```
git init
git add .
git commit -m "Primera version del tablero de Albion"
git branch -M main
git remote add origin https://github.com/snake1515/TU_REPO.git
git push -u origin main
```

## 3. Render

1. **New → Web Service**, conecta el repo.
2. Runtime: Python.
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app`
5. En **Environment**, agrega:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `CRON_SECRET` (opcional — cualquier string random, protege el endpoint manual de actualización)

## 4. Cómo funciona el cron

Vive dentro del mismo proceso de Flask (APScheduler), igual que en dian-facturas — corre cada hora mientras el servicio esté despierto, y se duerme junto con Render en el free tier si no hay tráfico. Cuando entres a la página, el botón "Traer últimos precios" fuerza una actualización manual sin esperar al cron.

## 5. Primeros pasos después de desplegar

1. Abre la URL de Render.
2. Ajusta los sliders de riesgo por ciudad y dale "Guardar configuración" (queda en Supabase, no se pierde).
3. Dale clic a "Traer últimos precios" la primera vez, para no esperar una hora a que corra el cron solo.

## Notas

- El catálogo de items vive en `app.py` (lista `ITEMS`). Si quieres agregar o quitar items, se edita ahí y se hace push — no requiere tocar Supabase.
- La tabla `margenes_historico` crece indefinidamente con el tiempo. Si en unos meses quieres podarla, un `delete from margenes_historico where ts < now() - interval '90 days';` corrido cada tanto en el SQL Editor basta.
