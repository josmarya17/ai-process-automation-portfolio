# Guía del Sistema SEO Auto Analyst 🚀

Este documento sirve como manual técnico y funcional para el sistema de automatización SEO.

## 📝 Descripción General
El **SEO Auto Analyst** es una herramienta de Inteligencia Business-driven diseñada para centralizar, analizar y reportar el desempeño SEO mensual de múltiples clientes de forma automatizada. 

El sistema extrae métricas de fuentes oficiales de Google (GSC y GA4) y las combina con datos personalizados en Google Sheets (Backlinks, PageSpeed, Moz) para que un **Director Estratégico (Gemini IA)** genere insights de alto nivel que se registran en una Bitácora centralizada.

---

## 🏗️ Qué Tiene (Stack Tecnológico)
- **Frontend**: Streamlit (Dashboard interactivo).
- **Backend**: Python 3.x con integración modular de `google-api-python-client`.
- **Inteligencia Artificial**: Google Gemini API (modelos 1.5, 2.5, 3.0/3.1).
- **Almacenamiento de Datos**: Google Sheets (como BBDD versátil).
- **Autenticación**: OAuth2 (User Credentials) para acceso nativo a propiedades de clientes.
- **Resiliencia**: Sistema de reintentos con `tenacity` y auto-detección de modelos de IA.

---

## ⚙️ Cómo Funciona (El Motor)
1.  **Selección de Cuenta**: El usuario elige la cuenta de Google (Token) desde la barra lateral.
2.  **Identificación de Cliente**: El sistema lee el "Inventario de Marcas" para saber qué propiedades de GSC y GA4 corresponden a cada cliente.
3.  **Extracción de Mes Natural Cerrado**:
    -   El sistema calcula el primer y último día del mes anterior completo.
    -   Extrae Clics, Impresiones, CTR y Posición (GSC).
    -   Extrae Usuarios, Sesiones y canales de conversión (GA4).
    -   Consulta datos de apoyo (Backlinks, Competidores, DA) desde Sheets específicos.
4.  **Análisis Estratégico**:
    -   Los datos se limpian y se envían a Gemini con una "Persona" de **Director Senior SEO**.
    -   La IA no solo resume datos, sino que identifica el **Impacto del Contenido** y los **Retos del Negocio**.
5.  **Registro en Bitácora**: Se guarda una fila nueva con la fecha del 1º del mes analizado, asegurando un histórico limpio.

---

## 📂 Requisitos para que funcione
1.  **Secretos de Streamlit (o .env local)**:
    -   `API_GEMINI`: Tu clave de Google AI Studio.
    -   `CLIENT_SECRET`: Tu JSON de cliente de Google Cloud.
    -   `token_wac.json`: Token de acceso generado vía OAuth2.
2.  **Google Cloud Project**: Con las APIs de Search Console, Google Analytics Data y Google Sheets habilitadas.
3.  **Google Sheets de Configuración**: Deben seguir la estructura de columnas definida en `config.py` y el script de extracción.

---

## 🚀 Funcionalidades Especiales
- **Caché Inteligente**: Los datos se guardan en memoria por 10 minutos para evitar saturar las cuotas de Google.
- **Auto-Detección de IA**: El bot escanea tu cuenta de Gemini para usar siempre el modelo más avanzado disponible (ej: 2.5 o 3.0 flash).
- **Modo Detective**: Si falta una pestaña en el Excel, el bot te avisa cuáles están disponibles para que puedas corregir el error rápidamente.
