chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "getUserInfo") {
    console.log("BG: Recibida solicitud getUserInfo");
    chrome.identity.getProfileUserInfo({ accountStatus: 'ANY' })
      .then((userInfo) => {
        console.log("BG: userInfo recuperado:", userInfo);
        sendResponse(userInfo);
      })
      .catch((err) => {
        console.error("BG: Error recuperando userInfo:", err);
        sendResponse(null);
      });
    return true; // Mantiene el canal abierto para respuesta asíncrona
  }
});
