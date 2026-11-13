# Ebstian v1 — primera entrega

Incluye una homepage pública responsive y la separación inicial entre Ebstian y ST Monitor.

## Archivos
- `app.py`: versión de tu Flask con `/` público y `/private` para ST Monitor.
- `templates/index.html`: homepage pública.
- `static/css/main.css`: sistema visual responsive.
- `static/js/main.js`: reloj, menú móvil y contenido aleatorio.
- `static/js/terminal.js`: terminal interactiva.

## Integración
1. Haz backup de tu `app.py` actual.
2. Reemplaza `app.py` por el incluido, conservando `dashboard.html`, `sites.json` y el resto de tus archivos.
3. Copia `templates/index.html` a `templates/`.
4. Copia `static/css/` y `static/js/` dentro de tu carpeta `static/`.
5. Confirma que `APP_PASSWORD` y `SECRET_KEY` estén configuradas en Railway.
6. Confirma que `requirements.txt` incluya `gunicorn` y las dependencias que ya usa ST Monitor.
7. Haz commit y push.

## Rutas
- `/`: homepage pública.
- `/login`: acceso privado.
- `/private`: dashboard ST Monitor (requiere sesión).
- `/logout`: cierra sesión y vuelve a la homepage.

## Notas
- Esta entrega todavía no conecta PostgreSQL; no crea ni modifica tablas.
- El middleware falla de forma cerrada si `APP_PASSWORD` no está configurada.
- Los reportes de clientes conservan el acceso por token.
- La terminal `login` navega a `/login`; no es un mecanismo de seguridad. La protección real está en Flask.
- El reloj usa la zona horaria del navegador.
