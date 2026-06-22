# Despliegue en Vercel

## Arquitectura de produccion

El repositorio es un monorepo:

- `frontend/`: Next.js 16.2.9 con App Router. Este servicio se despliega en Vercel.
- `backend/`: FastAPI, PostgreSQL con pgvector, Redis y almacenamiento de documentos. Este servicio no debe desplegarse como una funcion Vercel porque requiere procesos y almacenamiento persistentes.

La arquitectura recomendada es:

```text
similaritycheck.genevidence.com -> Vercel / Next.js
api-similaritycheck.genevidence.com -> Backend Docker persistente
                                      -> PostgreSQL + pgvector
                                      -> Redis
                                      -> volumen u object storage
```

El frontend no quedara funcional para login, documentos y reportes hasta que `NEXT_PUBLIC_API_BASE_URL` apunte a un backend HTTPS desplegado.

## 1. Publicar el codigo en GitHub

El repositorio remoto `jfchoez/genevidence-similarity-check` estaba vacio al preparar esta version. Antes de importar en Vercel, subir el contenido de este workspace a la rama principal del repositorio.

No subir archivos `.env`, contrasenas, tokens, documentos de usuarios ni directorios de almacenamiento.

## 2. Importar en Vercel

1. Entrar en Vercel y seleccionar **Add New > Project**.
2. Importar `jfchoez/genevidence-similarity-check` desde GitHub.
3. En **Root Directory**, seleccionar `frontend`.
4. Confirmar **Framework Preset: Next.js**.
5. Usar **Install Command: `npm ci`**.
6. Usar **Build Command: `npm run build`**.
7. No configurar manualmente Output Directory. Vercel usa `.next` mediante su integracion de Next.js.
8. El proyecto usa el runtime Node.js estandar de Vercel. `package.json` requiere Node.js 20.9 o superior.

No se necesita `vercel.json` para esta arquitectura.

## 3. Variables de entorno en Vercel

Configurar estas variables para Production, Preview y Development cuando corresponda:

| Variable | Valor de produccion |
| --- | --- |
| `NEXT_PUBLIC_APP_URL` | `https://similaritycheck.genevidence.com` |
| `NEXT_PUBLIC_SITE_URL` | `https://similaritycheck.genevidence.com` |
| `NEXT_PUBLIC_API_BASE_URL` | URL HTTPS del backend, por ejemplo `https://api-similaritycheck.genevidence.com` |
| `APP_NAME` | `Genevidence Similarity Check` |

Despues de cambiar una variable `NEXT_PUBLIC_*`, ejecutar un nuevo deployment porque Next.js incorpora esas variables durante el build.

No colocar en Vercel las credenciales privadas del backend si Vercel solo aloja el frontend.

## 4. Variables del backend

Configurar en el proveedor donde se ejecute FastAPI:

| Variable | Proposito |
| --- | --- |
| `DATABASE_URL` | PostgreSQL administrado con extension pgvector |
| `REDIS_URL` | Redis administrado |
| `JWT_SECRET` | Secreto aleatorio largo; nunca exponer al frontend |
| `JWT_ALGORITHM` | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Duracion de sesion |
| `MAX_UPLOAD_MB` | Limite de carga |
| `STORAGE_DIR` | Volumen persistente para documentos |
| `BACKEND_CORS_ORIGINS` | `https://similaritycheck.genevidence.com` |
| `AUTO_CREATE_TABLES` | `false` despues de aplicar Alembic |
| `SEMANTIC_ENABLED` | `false` inicialmente; requiere imagen con sentence-transformers |

Antes de iniciar el backend de produccion:

```bash
alembic upgrade head
```

El almacenamiento local efimero de un contenedor no es suficiente para documentos. Configurar un volumen persistente o adaptar `STORAGE_DIR` a object storage antes de aceptar archivos reales.

## 5. Conectar el dominio en Vercel

1. Abrir el proyecto en Vercel.
2. Ir a **Settings > Domains**.
3. Agregar `similaritycheck.genevidence.com`.
4. Vercel mostrara el registro DNS requerido.
5. Mantener abierta esa pantalla hasta completar Hostinger.

## 6. Crear el DNS en Hostinger

1. Abrir Hostinger y entrar a la zona DNS de `genevidence.com`.
2. Eliminar registros A, AAAA o CNAME existentes que entren en conflicto con `similaritycheck`.
3. Crear exactamente el registro indicado por Vercel.
4. Para un subdominio, Vercel normalmente solicita un CNAME:
   - Tipo: `CNAME`
   - Nombre/Host: `similaritycheck`
   - Destino: el valor mostrado por Vercel, frecuentemente `cname.vercel-dns.com`
   - TTL: valor predeterminado de Hostinger
5. Si Vercel muestra un valor diferente, usar el valor de su panel, no el ejemplo de esta guia.
6. Esperar la verificacion DNS y confirmar que Vercel marque el dominio como valido.

Vercel emitira y renovara HTTPS automaticamente cuando el DNS sea correcto.

## 7. Verificar SEO tecnico

Despues del deployment, abrir:

- `https://similaritycheck.genevidence.com/robots.txt`
- `https://similaritycheck.genevidence.com/sitemap.xml`

El sitemap debe incluir solamente:

- `/`
- `/features`
- `/pricing`
- `/login`
- `/register`

No debe incluir dashboard, admin, API, documentos ni reportes.

Las rutas privadas usan el Proxy de Next.js, validan la cookie `genevidence_token` contra `GET /auth/me` y responden con `X-Robots-Tag: noindex, nofollow, noarchive`. FastAPI sigue siendo la autoridad final: cada endpoint privado tambien valida el JWT.

## 8. Google Search Console

1. Abrir Google Search Console.
2. Agregar una propiedad de dominio para `genevidence.com` o una propiedad de prefijo para `https://similaritycheck.genevidence.com`.
3. Completar la verificacion solicitada. Una propiedad de dominio normalmente requiere un registro TXT en Hostinger.
4. Entrar en **Sitemaps**.
5. Enviar `https://similaritycheck.genevidence.com/sitemap.xml`.
6. Confirmar que Google lo procese sin rutas privadas.

## 9. Favicon

No se encontro un favicon cuadrado dedicado. El logo horizontal se usa para Open Graph. Para agregar favicon, colocar un PNG cuadrado de 512 x 512 en:

```text
frontend/app/icon.png
```

Next.js lo publicara automaticamente como icono del sitio.

## Checklist final

- [ ] Codigo subido a `jfchoez/genevidence-similarity-check`.
- [x] Build correcto con `npm run build`.
- [ ] Root Directory de Vercel configurado como `frontend`.
- [ ] Variables de entorno configuradas.
- [ ] Backend HTTPS desplegado y accesible.
- [ ] PostgreSQL/pgvector, Redis y storage persistente configurados.
- [ ] Dominio `similaritycheck.genevidence.com` conectado.
- [ ] HTTPS activo.
- [x] Dashboard y rutas privadas protegidas en el frontend y mediante JWT en FastAPI.
- [ ] Sitemap disponible.
- [ ] Robots.txt disponible.
- [ ] Google Search Console configurado.
