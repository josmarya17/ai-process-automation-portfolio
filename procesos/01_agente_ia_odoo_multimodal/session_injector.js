(function() {
  if (window.odoo && window.odoo.session_info) {
    window.postMessage({
      type: "ODOO_SESSION_INFO",
      session_info: {
        username: window.odoo.session_info.username,
        name: window.odoo.session_info.name
      }
    }, "*");
  }
})();
