# Plan de Despliegue en Producción: Xara IA en AWS

Este documento establece la estrategia paso a paso para trasladar la arquitectura actual del asistente de IA (**Xara**) a una infraestructura de producción en **Amazon Web Services (AWS)** de forma segura y controlada, asegurando el cumplimiento de las políticas corporativas de Google Workspace y Odoo.

---

## 1. Arquitectura de Infraestructura en AWS
Para garantizar escalabilidad, estabilidad y alta disponibilidad, se propone la siguiente arquitectura estándar:

```
[Navegadores de Usuarios (Odoo)] 
       │ (HTTPS - Puerto 443)
       ▼
[AWS Route 53 (xara-api.Empresa Demo.com)]
       │
       ▼
[AWS ALB (Application Load Balancer)] <─── SSL Terminado en AWS Certificate Manager (ACM)
       │
       ▼ (HTTP - Puerto 8000)
[AWS EC2 (Instancia de Backend)] <─── Dentro de una VPC (Subnet Privada o Pública Restringida)
```

### Componentes de AWS:
1. **Cómputo**: Una instancia de AWS EC2 (t3.small o t3.medium con Ubuntu Server 22.04 LTS). Opcionalmente, para un flujo contenedorizado, AWS ECS con Fargate.
2. **DNS & Dominio**: Registro CNAME en AWS Route 53 apuntando al Load Balancer (ej. `xara-api.Empresa Demo.com`).
3. **Cifrado en Tránsito (SSL/TLS)**: Certificado SSL emitido de forma gratuita por AWS Certificate Manager (ACM) e instalado en el Load Balancer.

---

## 2. Parámetros de Seguridad de Red y API (Protección Externa)
Dado que el servidor backend procesará información corporativa sensible, es crítico limitar su exposición externa:

### A. Restricción de Orígenes (CORS)
En el archivo `backend/app.py`, debes cambiar la política de CORS para restringir las llamadas del navegador únicamente a tus instancias de Odoo.
* **Código Actual**: `allow_origins=["*"]` (Permite peticiones desde cualquier sitio).
* **Configuración en Producción**:
  ```python
  app.add_middleware(
      CORSMiddleware,
      allow_origins=[
          "https://your-company.odoo.com",
          "https://your-company.odoo.com",
          "https://farmacias-Enterprise SGC.odoo.com" # Agrega los dominios de Odoo productivos
      ],
      allow_credentials=True,
      allow_methods=["GET", "POST", "OPTIONS"],
      allow_headers=["*"],
  )
  ```

### B. Autenticación por Cabecera (Shared Secret)
Para evitar que un tercero llame directamente a la API `/webhook` (incluso con el CORS restringido, los ataques curl directo son posibles), debemos validar una clave secreta (Token de API) en cada request:
1. **En la Extensión (content.js)**: Añadir una cabecera personalizada en la petición fetch:
   ```javascript
   headers: {
     'Content-Type': 'application/json',
     'X-Xara-Auth-Token': 'TU_TOKEN_SECRETO_CORPORATIVO'
   }
   ```
2. **En el Backend (app.py)**: Añadir un Middleware de Seguridad o una dependencia en FastAPI que verifique dicha cabecera:
   ```python
   from fastapi import Header

   async def validar_token_xara(x_xara_auth_token: str = Header(...)):
       if x_xara_auth_token != "TU_TOKEN_SECRETO_CORPORATIVO":
           raise HTTPException(status_code=403, detail="Acceso denegado: Token inválido.")
   ```

### C. Configuración de Grupo de Seguridad (Security Group) en AWS
* **Regla de Entrada en Load Balancer (ALB)**: Aceptar puerto `443` (HTTPS) de todo el mundo (`0.0.0.0/0`) o limitar únicamente al bloque de IPs públicas de la red interna de Empresa Demo.
* **Regla de Entrada en la Instancia EC2**: Permitir tráfico en el puerto `8000` **únicamente** desde la IP interna del Load Balancer (ALB). La instancia EC2 nunca debe estar expuesta directamente al internet público en el puerto del backend.

---

## 3. Configuración en Google Workspace (Admin del Dominio)
Para habilitar el funcionamiento completo del calendario (creación de salas de Google Meet, invitaciones automáticas bidireccionales y lectura de agendas ajenas), el Administrador del Dominio en Google Workspace debe configurar la **Delegación de Autoridad en todo el Dominio (DWD)**.

### Pasos obligatorios para el Administrador de TI:
1. Iniciar sesión en la [Consola de Administración de Google](https://admin.google.com).
2. Ir a **Menú** > **Seguridad** > **Control de acceso y de APIs** > **Delegación de autoridad en todo el dominio**.
3. Hacer clic en **Añadir nuevo**.
4. Rellenar el formulario con los siguientes datos del archivo `agenteia.json`:
   * **ID de cliente**: `111335540226615983390`
   * **Ámbitos de OAuth (Scopes)**: Copiar y pegar la siguiente lista de URLs separadas por comas:
     ```
     https://www.googleapis.com/auth/calendar,
     https://www.googleapis.com/auth/calendar.events,
     https://www.googleapis.com/auth/drive.readonly,
     https://www.googleapis.com/auth/spreadsheets.readonly
     ```
5. Hacer clic en **Autorizar**.
6. *Nota*: Los permisos de delegación pueden tardar entre 10 y 30 minutos en propagarse por los servidores de Google.

A partir de este momento, el backend podrá impersonar a cualquier usuario (ej. `josmary.pinto@Empresa Demo.com`) de manera invisible sin requerir que los usuarios compartan sus calendarios manualmente.

---

## 4. Despliegue de la Extensión en los Navegadores de la Empresa
Para evitar que cada usuario tenga que habilitar el "Modo Desarrollador" y cargar la carpeta descomprimida en su Chrome (lo cual es inseguro y propenso a desconfiguraciones), existen dos métodos corporativos recomendados:

### Opción A: Distribución Privada en Chrome Web Store (Recomendado)
1. Registrar una cuenta de desarrollador de Google Chrome.
2. Subir el proyecto empaquetado (como archivo `.zip` que contenga `manifest.json`, `content.js`, `background.js`, `session_injector.js`, `styles.css` e imágenes).
3. En la configuración de visibilidad del Web Store, seleccionar **Privado (Visibilidad limitada al dominio de tu organización)**. Esto restringe la descarga única y exclusivamente a usuarios logueados en Chrome con sus cuentas `@Empresa Demo.com` o `@Enterprise SGC.com`.
4. El Administrador de Google Workspace puede forzar la instalación remota de la extensión a todos los usuarios del dominio de la empresa de forma automática desde la sección **Dispositivos** > **Chrome** > **Aplicaciones y Extensiones** en la consola de Google Workspace Admin.

### Opción B: Despliegue por Directiva de Grupo (GPO - Active Directory)
Si la empresa gestiona las computadoras de los empleados mediante Windows Server Active Directory (AD):
1. Alojar la extensión empaquetada (`.crx`) y un archivo XML de actualización (`update.xml`) en un servidor IIS o Apache en la intranet corporativa.
2. Utilizar las Plantillas Administrativas de Google Chrome para Directivas de Grupo (GPO).
3. Configurar la directiva **ExtensionInstallForceList** e ingresar la ruta interna de descarga y el ID de la extensión.
4. Las máquinas de los usuarios descargarán e instalarán la extensión silenciosamente en segundo plano sin intervención humana.
