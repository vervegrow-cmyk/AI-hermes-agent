(function() {
      const importPath = /*@__PURE__*/ JSON.parse('"contentScripts/mainUI.js"');
      import(chrome.runtime.getURL(importPath));
    })();