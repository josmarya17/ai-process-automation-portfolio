(function () {
  // Evitar doble inyección (remover el anterior si existe al recargar la extensión)
  const existingRoot = document.getElementById('pharmacy-copilot-root');
  if (existingRoot) existingRoot.remove();

  // =========================================================================
  // ⚙️ CONFIGURACIÓN DEL AGENTE DE IA
  // CONFIGURACIÓN: Reemplaza esta URL con la URL del Webhook de tu servidor local o nube
  // =========================================================================
  const N8N_WEBHOOK_URL = 'http://localhost:8000/webhook';

  // Sugerencias personalizadas para cada pestaña
  const SUGGESTIONS = {
    sistema: [
      { text: '¿Cómo registrar una factura de proveedor?', query: '¿Cómo registrar una factura de proveedor en Odoo v17?' },
      { text: '¿Cómo recibir mercadería en inventario?', query: '¿Cómo recibir productos en Almacén en Odoo v17?' },
      { text: 'Estados de facturas de compra', query: '¿Cuáles son los estados contables de una factura de proveedor?' }
    ],
    procesos: [
      { text: 'Ver manual de arqueo de caja', query: 'Quiero consultar sobre procesos o normas de Droguería Nena: arqueo de caja' },
      { text: 'Ver manual de diferencias de caja', query: 'Quiero consultar sobre procesos o normas de Droguería Nena: identificación de diferencias' },
      { text: 'Conciliación de pagos Cashea', query: 'Quiero consultar sobre procesos o normas de Droguería Nena: conciliación de pagos Cashea' }
    ],
    usuario: [
      { text: 'Buscar correo de algún usuario?', query: 'Quiero consultar sobre los datos o disponibilidad de un usuario: correo de ' },
      { text: 'Buscar disponibilidad de algún usuario', query: 'Quiero consultar sobre los datos o disponibilidad de un usuario: disponibilidad de ' },
      { text: '¿Quién es el Regente de Calidad?', query: 'Quiero consultar sobre los datos o disponibilidad de un usuario: ¿Quién es el Regente de Calidad?' }
    ]
  };

  const TITLES = {
    sistema: {
      title: '¿Qué duda tienes sobre Odoo v17?',
      desc: 'Selecciona una sugerencia o escribe tu duda funcional:'
    },
    procesos: {
      title: '¿Qué manual o proceso buscas?',
      desc: 'Selecciona un manual de Droguería Nena o escribe tu consulta:'
    },
    usuario: {
      title: '¿A quién del equipo deseas contactar?',
      desc: 'Busca por nombre, área o disponibilidad de agenda:'
    }
  };

  // Variables globales de sesión del usuario
  let userEmail = "";
  let userName = "";
  let chatInitialized = false;

  // Función para inicializar con un email y nombre válidos
  function tryInitialize(email, name) {
    if (chatInitialized) return;
    const emailLower = email.toLowerCase();
    if (emailLower.endsWith("@dronena.com") || emailLower.endsWith("@xana.com")) {
      userEmail = emailLower;
      userName = name || formatNameFromEmail(emailLower);
      chatInitialized = true;
      console.log(`Xara: Iniciando con usuario validado: ${userName} (${userEmail})`);
      initChat();
    } else {
      console.warn(`Xara: Acceso denegado para el correo: ${emailLower}. Solo se permiten dominios @dronena.com o @xana.com.`);
    }
  }

  // 1. Escuchar el mensaje inyectado desde el contexto de la página (MAIN world)
  window.addEventListener("message", (event) => {
    if (event.source === window && event.data && event.data.type === "ODOO_SESSION_INFO") {
      const session = event.data.session_info;
      console.log("Xara: Datos de sesión de Odoo recibidos:", session);
      if (session && session.username) {
        tryInitialize(session.username, session.name);
      }
    }
  });

  // Inyectar script para leer window.odoo.session_info (usando archivo para cumplir con CSP)
  try {
    const script = document.createElement('script');
    script.src = chrome.runtime.getURL('session_injector.js');
    (document.head || document.documentElement).appendChild(script);
    script.onload = function() {
      script.remove();
    };
  } catch (err) {
    console.error("Xara: Error inyectando script de sesión:", err);
  }

  // 2. Fallback: Consultar identidad en el perfil de Chrome (por si Odoo no ha cargado session_info o falla)
  setTimeout(() => {
    if (!chatInitialized) {
      console.log("Xara: Odoo session_info no detectado o no válido, intentando con Chrome Identity...");
      chrome.runtime.sendMessage({ action: "getUserInfo" }, (userInfo) => {
        console.log("Xara: userInfo de Chrome recibido:", userInfo);
        if (userInfo && userInfo.email) {
          tryInitialize(userInfo.email, formatNameFromEmail(userInfo.email));
        } else {
          // Si ambos fallan, mostrar advertencia en la consola
          setTimeout(() => {
            if (!chatInitialized) {
              console.warn("Xara: No se pudo verificar la sesión ni de Odoo ni del perfil de Chrome con dominios autorizados.");
            }
          }, 2000);
        }
      });
    }
  }, 1000);

  function formatNameFromEmail(email) {
    const localPart = email.split('@')[0];
    const parts = localPart.split('.');
    return parts.map(part => part.charAt(0).toUpperCase() + part.slice(1)).join(' ');
  }

  function initChat() {
    // Crear elemento raíz aislado en el DOM de Odoo
    const root = document.createElement('div');
    root.id = 'pharmacy-copilot-root';
    document.body.appendChild(root);

  // Inyectar HTML básico (FAB y Panel de Chat)
  root.innerHTML = `
    <!-- Botón Flotante (FAB) -->
    <div class="pharmacy-fab" id="pharmacy-fab" title="Xara">
      <img src="${chrome.runtime.getURL('icono_chat.png')}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 50%;" alt="Xara">
      <div class="pharmacy-fab-indicator"></div>
    </div>

    <!-- Panel de Chat -->
    <div class="pharmacy-chat-panel" id="pharmacy-chat-panel">
      <!-- Cabecera -->
      <div class="pharmacy-header">
        <div class="pharmacy-header-info">
          <div class="pharmacy-avatar" style="overflow: hidden; display: flex; align-items: center; justify-content: center; background: #ffffff; padding: 2px;">
            <img src="${chrome.runtime.getURL('Logo_XANA.jpg')}" style="width: 100%; height: 100%; object-fit: contain; border-radius: 6px;" alt="XANA">
          </div>
          <div class="pharmacy-title-area">
            <h3>Xara</h3>
            <div class="pharmacy-status">
              <div class="pharmacy-status-dot"></div>
              <span>Asistenta Odoo y Procesos</span>
            </div>
          </div>
        </div>
        <button class="pharmacy-close-btn" id="pharmacy-close-btn" title="Cerrar">
          <svg viewBox="0 0 24 24">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>

      <!-- Selector de Pestañas -->
      <div class="pharmacy-tabs" id="pharmacy-tabs">
        <button class="pharmacy-tab active" data-tab="sistema">
          <svg viewBox="0 0 24 24" class="tab-icon"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="2" y1="10" x2="22" y2="10"></line><path d="M12 17v4M8 21h8"></path></svg>
          Sistema
        </button>
        <button class="pharmacy-tab" data-tab="procesos">
          <svg viewBox="0 0 24 24" class="tab-icon"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line></svg>
          Procesos
        </button>
        <button class="pharmacy-tab" data-tab="usuario">
          <svg viewBox="0 0 24 24" class="tab-icon"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
          Usuarios
        </button>
      </div>

      <!-- Historial de Mensajes -->
      <div class="pharmacy-messages" id="pharmacy-messages">
        <!-- Mensaje de bienvenida -->
        <div class="pharmacy-msg-wrapper agent pharmacy-welcome-wrapper">
          <div class="pharmacy-msg-bubble pharmacy-welcome-msg">
            Hola <strong>${userName.split(' ')[0]}</strong>, soy <strong>Xara</strong> 👋, estoy lista para asistirte con lo que necesites.
          </div>
          <div class="pharmacy-msg-meta">${getFormattedTime()}</div>
        </div>

        <!-- Tarjeta de bienvenida con sugerencias -->
        <div class="pharmacy-welcome-card">
          <h4 id="pharmacy-welcome-title">¿Qué duda tienes sobre Odoo v17?</h4>
          <p id="pharmacy-welcome-desc">Selecciona una sugerencia o escribe tu duda funcional:</p>
          
          <div class="pharmacy-quick-actions" id="pharmacy-quick-actions">
            <!-- Se cargan dinámicamente según la pestaña activa -->
          </div>
        </div>
      </div>

      <!-- Barra de Entrada de Mensaje -->
      <div class="pharmacy-input-bar">
        <div class="pharmacy-input-wrapper">
          <input type="text" class="pharmacy-input" id="pharmacy-input" placeholder="¿Por dónde empezamos?" autocomplete="off">
        </div>
        <button class="pharmacy-send-btn" id="pharmacy-send-btn" title="Enviar">
          <svg viewBox="0 0 24 24">
            <line x1="22" y1="2" x2="11" y2="13"></line>
            <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
          </svg>
        </button>
      </div>

      <!-- Pie de página -->
      <div class="pharmacy-footer">
        POWERED BY N8N AI • n8n.wellu.io
      </div>
    </div>
  `;

  // Referencias a elementos del DOM
  const fab = document.getElementById('pharmacy-fab');
  const panel = document.getElementById('pharmacy-chat-panel');
  const closeBtn = document.getElementById('pharmacy-close-btn');
  const messagesDiv = document.getElementById('pharmacy-messages');
  const inputEl = document.getElementById('pharmacy-input');
  const sendBtn = document.getElementById('pharmacy-send-btn');
  const tabs = document.querySelectorAll('.pharmacy-tab');

  let activeCategory = 'sistema';

  // Configurar placeholder inicial
  inputEl.placeholder = 'Consultar sobre el sistema Odoo...';
  
  // Cargar sugerencias por defecto (Sistema)
  updateSuggestions('sistema');

  // Lógica de cambio de pestaña
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      activeCategory = tab.getAttribute('data-tab');
      
      // Cambiar el placeholder según la pestaña activa
      if (activeCategory === 'sistema') {
        inputEl.placeholder = 'Consultar sobre el sistema Odoo...';
      } else if (activeCategory === 'procesos') {
        inputEl.placeholder = 'Buscar procesos y manuales internos...';
      } else if (activeCategory === 'usuario') {
        inputEl.placeholder = 'Buscar disponibilidad o datos de usuario...';
      }

      // Actualizar títulos y botones de sugerencias
      updateSuggestions(activeCategory);
    });
  });

  // Lógica de apertura/cierre del chat
  fab.addEventListener('click', () => {
    panel.classList.toggle('active');
    if (panel.classList.contains('active')) {
      inputEl.focus();
    }
  });

  closeBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    panel.classList.remove('active');
  });

  // Listener para el botón enviar y enter
  sendBtn.addEventListener('click', handleSendMessage);
  inputEl.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      handleSendMessage();
    }
  });

  // Action Pills delegación con sincronización de pestañas
  messagesDiv.addEventListener('click', (e) => {
    const pill = e.target.closest('.pharmacy-btn-pill');
    if (pill) {
      const msgText = pill.getAttribute('data-msg');
      if (msgText) {
        // Encontrar la categoría correspondiente
        let cat = 'sistema';
        if (msgText.includes('procesos')) {
          cat = 'procesos';
        } else if (msgText.includes('usuario')) {
          cat = 'usuario';
        }
        
        // Activar la pestaña correspondiente
        const targetTab = document.querySelector(`.pharmacy-tab[data-tab="${cat}"]`);
        if (targetTab) {
          targetTab.click();
        }

        inputEl.value = msgText;
        handleSendMessage();
      }
    }
  });

  // Función para enviar mensajes a n8n
  async function handleSendMessage() {
    const text = inputEl.value.trim();
    if (!text) return;

    // 1. Mostrar mensaje del usuario en el chat
    addMessage(text, 'user');
    inputEl.value = '';
    scrollToBottom();

    // 2. Mostrar indicador de "escribiendo"
    const typingIndicator = showTypingIndicator();

    try {
      // 3. Realizar la petición HTTP real a tu n8n / servidor Python
      const response = await fetch(N8N_WEBHOOK_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message: text,
          category: activeCategory,
          user: userName,
          email: userEmail,
          timestamp: new Date().toISOString(),
          sessionId: getSessionId()
        })
      });

      // Remover el indicador de carga
      typingIndicator.remove();

      if (!response.ok) {
        throw new Error(`Error en el servidor n8n (HTTP Status ${response.status})`);
      }

      // 4. Intentar parsear respuesta (soporta formato texto plano o JSON estructurado)
      const contentType = response.headers.get('content-type') || '';
      let answerText = '';

      if (contentType.includes('application/json')) {
        const jsonResponse = await response.json();
        // n8n AI Agent suele retornar la respuesta en campos como 'output', 'text' o 'response'
        answerText = jsonResponse.output || jsonResponse.text || jsonResponse.response || JSON.stringify(jsonResponse);
      } else {
        answerText = await response.text();
      }

      // 5. Agregar respuesta del cerebro real
      addMessage(answerText, 'agent');

    } catch (error) {
      // Remover indicador en caso de fallo
      typingIndicator.remove();

      // ⚠️ Mensaje de error amigable con diagnóstico de CORS/Conectividad
      const errorMessage = `
        <div style="color: #ef4444; font-weight: 500;">
          ⚠️ No se pudo conectar con el Cerebro en n8n
        </div>
        <div style="font-size: 11px; margin-top: 8px; color: #94a3b8; line-height: 1.4;">
          <strong>Causas comunes:</strong><br>
          1. ¿n8n está cerrado? Inícialo con <code>n8n start</code> en tu terminal.<br>
          2. ¿URL incorrecta? Valida si tu puerto es el 5678 y que la URL coincide con la de tu webhook activo.<br>
          3. <strong>¿Bloqueo de CORS?</strong> Activa los encabezados de respuesta CORS en tu nodo Webhook de n8n (Agrega la propiedad <code>Access-Control-Allow-Origin: *</code> en las opciones del nodo Webhook).<br><br>
          <em>Detalle del error técnico: ${error.message}</em>
        </div>
      `;
      addMessage(errorMessage, 'agent');
    }

    scrollToBottom();
  }

  // Auxiliares del DOM
  function addMessage(text, sender) {
    const msgWrapper = document.createElement('div');
    msgWrapper.className = `pharmacy-msg-wrapper ${sender}`;

    const msgBubble = document.createElement('div');
    msgBubble.className = 'pharmacy-msg-bubble';
    msgBubble.innerHTML = text;

    const msgMeta = document.createElement('div');
    msgMeta.className = 'pharmacy-msg-meta';
    msgMeta.innerText = getFormattedTime();

    msgWrapper.appendChild(msgBubble);
    msgWrapper.appendChild(msgMeta);
    messagesDiv.appendChild(msgWrapper);
  }

  function showTypingIndicator() {
    const indicator = document.createElement('div');
    indicator.className = 'pharmacy-typing-indicator';
    indicator.innerHTML = `
      <div class="pharmacy-dot"></div>
      <div class="pharmacy-dot"></div>
      <div class="pharmacy-dot"></div>
    `;
    messagesDiv.appendChild(indicator);
    scrollToBottom();
    return indicator;
  }

  function getFormattedTime() {
    const now = new Date();
    return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  function scrollToBottom() {
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
  }

  // Actualizar sugerencias dinámicamente según la categoría activa
  function updateSuggestions(category) {
    const container = document.getElementById('pharmacy-quick-actions');
    const titleEl = document.getElementById('pharmacy-welcome-title');
    const descEl = document.getElementById('pharmacy-welcome-desc');
    
    if (titleEl && descEl && TITLES[category]) {
      titleEl.innerText = TITLES[category].title;
      descEl.innerText = TITLES[category].desc;
    }
    
    if (container) {
      container.innerHTML = '';
      const list = SUGGESTIONS[category] || [];
      
      let iconSvg = '';
      if (category === 'sistema') {
        iconSvg = `<svg viewBox="0 0 24 24"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="2" y1="10" x2="22" y2="10"></line><path d="M12 17v4M8 21h8"></path></svg>`;
      } else if (category === 'procesos') {
        iconSvg = `<svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line></svg>`;
      } else if (category === 'usuario') {
        iconSvg = `<svg viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>`;
      }
      
      list.forEach(item => {
        const button = document.createElement('button');
        button.className = 'pharmacy-btn-pill';
        button.setAttribute('data-msg', item.query);
        button.innerHTML = `${iconSvg} ${item.text}`;
        container.appendChild(button);
      });
    }
  }

  function getSessionId() {
    let sid = localStorage.getItem('xara_session_id');
    if (!sid) {
      sid = 'session_' + Math.random().toString(36).substring(2, 11);
      localStorage.setItem('xara_session_id', sid);
    }
    return sid;
  }
  }
})();
