# Ebstian + ST Monitor — preparación para PostgreSQL

Esta entrega se aplica **encima del proyecto que ya está funcionando**. Conserva la homepage, login, dashboard y endpoints de ST Monitor. No incluye credenciales, `.env`, `sites.json`, `.git`, entornos virtuales ni backups.

## Cambios incluidos

- Configuración de Flask-SQLAlchemy y Flask-Migrate.
- Modelos iniciales para `artists`, `albums`, `collections`, `collection_items`, `random_entries`, `experiments` y `site_settings`.
- Conexión automática a `DATABASE_URL` (Railway PostgreSQL).
- Compatibilidad con `POSTGRES_URL` como alternativa.
- Conversión de `postgres://` / `postgresql://` a `postgresql+psycopg://`.
- Fallback local a SQLite si no hay URL de PostgreSQL.
- Spotify queda preparado con la variable global `SPOTIFY_URL`.
- Música actualizada: se agregan Fall Out Boy y DLD; se quitan Los Caligaris y Genitallica.
- `.gitignore` ampliado para excluir secretos, bases locales y entornos virtuales.

## Importante: conservar ST Monitor

Este paquete no contiene `sites.json` intencionalmente. **No lo reemplaces ni lo borres**: conserva el archivo actual de tu proyecto, ya que contiene la configuración de sitios y sus tokens de reportes.

Tampoco reemplaces `templates/dashboard.html`, los iconos ni otros archivos existentes que no estén incluidos en este paquete.

## Aplicar los cambios

1. Descarga y descomprime este paquete.
2. Haz una copia de seguridad de tu proyecto actual.
3. Copia los archivos de este paquete sobre tu proyecto actual, respetando las carpetas.
4. Conserva tu `sites.json` actual y las variables existentes de Railway.
5. Instala dependencias:

   ```bash
   pip install -r requirements.txt
   ```

## Crear la primera migración

Desde la raíz del proyecto, ejecuta una sola vez:

```bash
flask --app app db init
flask --app app db migrate -m "Initial Ebstian content schema"
flask --app app db upgrade
```

Esto crea la carpeta `migrations/` y aplica las tablas a la base configurada en el entorno local (SQLite si no existe `DATABASE_URL`).

Revisa la migración generada antes de continuar. Después agrega `migrations/` al repositorio y haz commit/push. **No generes una migración nueva en cada deploy.**

## Aplicar la migración en Railway

Verifica que el servicio PostgreSQL esté vinculado al servicio web y que exista la variable `DATABASE_URL`.

Después de subir `migrations/` al repositorio, configura temporalmente el comando de pre-deploy de Railway como:

```bash
flask --app app db upgrade
```

Si tu plan/configuración no tiene pre-deploy command, ejecuta ese comando desde la shell del servicio antes de usar las nuevas tablas. El comando es idempotente: aplica las migraciones pendientes.

Mantén el Start Command actual:

```bash
gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120
```

## Variables de entorno

Obligatorias (ya deben existir en Railway):

- `SECRET_KEY`
- `APP_PASSWORD`
- `DATABASE_URL` (proporcionada por Railway PostgreSQL)

Opcional:

- `SPOTIFY_URL`: URL pública de playlist, álbum o artista de Spotify.
- `GOOGLE_CREDENTIALS_JSON` o `GOOGLE_APPLICATION_CREDENTIALS`: credenciales de Google Analytics.
- `CACHE_TTL`: duración de caché de ST Monitor.

La playlist se integra automáticamente cuando agregues su enlace a `SPOTIFY_URL`. No necesitas otro cambio de código.

## Alcance y límites de esta etapa

- Las tablas quedan preparadas, pero todavía no se crea un panel CRUD para administrarlas.
- ST Monitor sigue leyendo y escribiendo su configuración en `sites.json`; no se migra a PostgreSQL en esta etapa.
- No se ejecuta `db.create_all()` al arrancar. El esquema se controla con migraciones.
- No se insertan datos de prueba ni artistas automáticamente.

## Seguridad del repositorio

El ZIP original incluía `.env`, `service-account.json`, `.git` y entornos virtuales. Esta entrega los excluye y amplía `.gitignore`.

Si esos archivos ya estaban versionados, `.gitignore` no los elimina del índice. Revisa:

```bash
git status
git ls-files .env service-account.json
```

Si aparecen como archivos rastreados, sácalos del índice sin borrar tus copias locales:

```bash
git rm --cached .env service-account.json
```

Si las credenciales llegaron a un repositorio público, rota la contraseña, `SECRET_KEY` y la clave de la cuenta de servicio de Google.
