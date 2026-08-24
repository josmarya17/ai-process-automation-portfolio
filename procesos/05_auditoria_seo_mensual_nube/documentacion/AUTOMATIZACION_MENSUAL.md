# Guía de Automatización Mensual (GitHub Actions) 🤖

Para que el sistema funcione solo cada mes sin costo y sin necesidad de tarjeta de crédito, usaremos **GitHub Actions**. Sigue estos pasos para configurar la "Caja Fuerte" de tus llaves.

---

## 🛑 PASO 0: Publicar App en Google (IMPORTANTE)
Antes de nada, asegúrate de que tu acceso a Google no caduque:
1.  Ve a [Google Cloud Console - OAuth Consent Screen](https://console.cloud.google.com/apis/credentials/consent).
2.  Dale al botón **"PASAR A PRODUCCIÓN"** (Publish App).
3.  Esto hará que tus credenciales duren para siempre.

---

## 🔐 PASO 1: Configurar los Secrets en GitHub
GitHub necesita tus llaves para entrar a Search Console y Analytics, pero las guardaremos bajo llave.

1.  Ve a tu repositorio en GitHub (en la web).
2.  Haz clic en **Settings** (Ajustes) en la barra superior.
3.  En el menú de la izquierda, busca **Secrets and variables** -> **Actions**.
4.  Haz clic en el botón verde **"New repository secret"**.

Deberás crear **3 secretos** exactamente con estos nombres:

| Nombre del Secreto | Qué contenido pegar |
| :--- | :--- |
| **`API_GEMINI`** | Tu clave de API de Gemini (la que ya tienes). |
| **`CLIENT_SECRET_JSON`** | Abre tu archivo `cloud/client_secret.json`, copia todo el texto y pégalo aquí. |
| **`TOKEN_WAC_JSON`** | Abre tu archivo `cloud/token_wac.json`, copia todo el texto y pégalo aquí. |

---

## 🚀 PASO 2: Verificar la automatización
Ya he creado el archivo de "Workflow" por ti. El bot tiene orden de despertarse el **día 1 de cada mes a las 8:00 AM**.

**Para probarlo ahora mismo manualmente:**
1.  Ve a la pestaña **Actions** en tu repositorio de GitHub.
2.  A la izquierda verás **"SEO Monthly Automated Analysis"**. Haz clic ahí.
3.  Verás un botón gris que dice **"Run workflow"**. Haz clic y dale a ejecutar.
4.  Podrás ver en tiempo real cómo el bot se conecta y actualiza la Bitácora.

---

## ✅ Beneficios de este método
- **Gratis Total**: GitHub te regala minutos de ejecución de sobra.
- **Sin Tarjeta**: No te pide datos bancarios.
- **Seguro**: Nadie puede ver tus llaves, ni siquiera tú después de guardarlas.

**¡Tu agencia ahora tiene un motor de análisis 100% autónomo!** 📊✨
