# Genevidence Similarity Check

Genevidence Similarity Check es una base SaaS multiusuario para revision academica de similitud textual en documentos biomedicos en espanol. La plataforma no declara plagio: muestra coincidencias, posibles parafrasis y fragmentos revisables para interpretacion humana.

## Alcance del MVP

- Registro, login JWT y roles `admin`, `reviewer`, `user`.
- Carga de documentos PDF y DOCX.
- Extraccion, limpieza, deteccion de secciones y segmentacion en chunks.
- Indexacion interna con fingerprints tipo winnowing por chunk.
- Generacion de reportes contra documentos internos previamente indexados.
- Reporte web con filtros por fuente, seccion, tipo de coincidencia y score minimo.
- Reporte PDF con portada, resumen ejecutivo, fuentes, secciones, detalle, metodologia y limitaciones.
- Sistema SaaS inicial con planes, suscripciones y creditos.
- Capa experimental de embeddings multilingues con `sentence-transformers` y almacenamiento `pgvector`.

## Advertencia etica

El reporte identifica similitudes textuales y requiere interpretacion academica. No constituye una determinacion automatica de plagio. Las posibles parafrasis semanticas son senales de revision, no evidencia concluyente de mala practica academica.

## Arquitectura

```text
backend/
  app/
    api/          FastAPI routes
    core/         config, db, seguridad
    models/       SQLAlchemy models
    schemas/      Pydantic schemas
    services/     NLP, reportes, PDF, billing
  alembic/        migraciones PostgreSQL/pgvector
  tests/          pruebas unitarias
frontend/
  app/            Next.js App Router
  components/     UI compartida
  lib/            cliente API
docker-compose.yml
```

## Ejecucion con Docker

```bash
docker compose up --build
```

Servicios:

- Backend y OpenAPI: puerto `8000` de la maquina de desarrollo.
- Frontend: puerto `3000` de la maquina de desarrollo.
- PostgreSQL + pgvector: puerto `5432`.
- Redis: puerto `6379`.

El primer usuario registrado se crea como `admin`. Los usuarios nuevos reciben creditos iniciales del plan `free`.

## Ejecucion local backend

```bash
cd backend
python -m venv .venv
. .venv/Scripts/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Para aplicar migraciones manualmente:

```bash
cd backend
alembic upgrade head
```

La app tambien puede crear tablas al arrancar si `AUTO_CREATE_TABLES=true`.

## Despliegue de produccion

El frontend Next.js esta preparado para Vercel usando `frontend` como Root Directory. FastAPI, PostgreSQL/pgvector, Redis y los documentos requieren infraestructura persistente separada. Consultar [DEPLOYMENT.md](DEPLOYMENT.md) para variables, dominio, DNS Hostinger, robots, sitemap y Google Search Console.

## Flujo de uso

1. Registrar un usuario.
2. Iniciar sesion.
3. Subir un documento PDF o DOCX.
4. Esperar estado `indexed`.
5. Subir otro documento.
6. Abrir el detalle y generar reporte.
7. Revisar coincidencias y descargar PDF.

## Endpoints principales

- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `POST /documents/upload`
- `GET /documents`
- `GET /documents/{document_id}`
- `POST /reports/{document_id}/generate?exclude_references=true`
- `GET /reports/{report_id}`
- `GET /reports/{report_id}/pdf`
- `GET /billing/credits`
- `POST /admin/users/{id}/credits`
- `GET /admin/reports`
- `GET /admin/documents`
- `GET /admin/stats`

## Metodologia de similitud textual

Al indexar un documento:

1. Se extrae texto de PDF/DOCX.
2. Se limpia el texto sin eliminar citas internas.
3. Se detectan secciones: resumen, introduccion, antecedentes, metodologia, resultados, discusion, referencias, anexos o seccion no detectada.
4. Se divide el documento en chunks de cerca de 150 palabras con solapamiento de 30.
5. Para cada chunk se generan k-grams de palabras.
6. Cada k-gram se hashea con BLAKE2b.
7. Se aplica winnowing con ventana configurable.
8. Se guardan fingerprints en `chunk_fingerprints` con `id`, `chunk_id`, `hash_value`, `position`.

Al generar un reporte:

1. Se buscan candidatos por fingerprints compartidos, evitando comparar todos los chunks contra todos.
2. Se calcula Jaccard sobre fingerprints.
3. Se calcula RapidFuzz `token_set_ratio`.
4. Se clasifica como:
   - `exact`: coincidencia literal.
   - `near_exact`: coincidencia casi literal.
   - `partial`: coincidencia parcial.
   - `possible_paraphrase`: posible parafrasis semantica.
5. Se calcula similitud global como palabras en chunks coincidentes sobre palabras totales.
6. Se calcula similitud excluyendo referencias y similitud por seccion.

## Frases metodologicas comunes

La lista editable esta en `backend/app/core/common_phrases.py`:

- estudio observacional
- diseno transversal
- se realizo un analisis descriptivo
- se considero estadisticamente significativo
- intervalo de confianza del 95%

Estas frases no se eliminan automaticamente del reporte. Se marcan como `frase metodologica comun`.

## Embeddings semanticos experimentales

La capa semantica usa `sentence-transformers` y `pgvector`. El modelo por defecto es `intfloat/multilingual-e5-base`.

Para activarla:

```env
SEMANTIC_ENABLED=true
SEMANTIC_MODEL_NAME=intfloat/multilingual-e5-base
SEMANTIC_EMBEDDING_DIMENSIONS=768
```

La imagen Docker normal omite PyTorch para mantener ligero el MVP. Para construir el backend con la capa semantica:

```bash
docker compose build --build-arg INSTALL_SEMANTIC=true backend
docker compose up -d
```

Una coincidencia se marca como `possible_paraphrase` solo si:

- `cosine_similarity >= 0.86`
- `fuzzy_score < 75`
- longitud minima del chunk >= 60 palabras

La deteccion semantica es experimental y debe interpretarse como senal de revision.

## Logica SaaS

Planes base:

- `free`
- `professional`
- `institutional`

Cada reporte consume 1 credito. El admin puede asignar creditos desde el panel o con `POST /admin/users/{id}/credits`.

Privacidad:

- Usuarios normales solo ven sus documentos y reportes.
- Admin puede ver estadisticas y listados generales.
- Documentos de otros usuarios pueden usarse para comparacion interna.
- En reportes con fuentes de otros usuarios, la fuente se muestra como `Documento interno #ID`.
- Los fragmentos de fuentes ajenas se recortan para mostrar solo lo necesario en revision.

## Pruebas

```bash
cd backend
pytest
```

Las pruebas cubren limpieza, segmentacion, secciones, fingerprints winnowing, Jaccard, textos copiados, cambios menores, textos no relacionados y reglas semanticas.

## Limitaciones actuales

- Solo compara contra documentos internos.
- No compara contra toda la web.
- No consulta PubMed, SciELO ni repositorios externos.
- No reemplaza revision academica humana.
- El porcentaje de similitud es aproximado.
- La deteccion semantica avanzada es experimental y esta desactivada por defecto.
- No incluye deteccion de texto generado por IA.
- El procesamiento se ejecuta con tareas de fondo FastAPI en este MVP; Redis queda preparado para evolucionar a worker dedicado.

## Roadmap

1. Worker Celery completo para extraccion e indexacion.
2. Busqueda web legal y repositorios abiertos.
3. Indexacion de tesis y documentos publicos.
4. Comparacion contra articulos cientificos open access.
5. Exclusion automatica de referencias Vancouver/APA.
6. Panel institucional avanzado.
7. API para universidades.
8. Facturacion con proveedor de pagos.
9. Recomendaciones de citacion y correccion academica.
