(function() {
      const importPath = /*@__PURE__*/ JSON.parse('"contentScripts/authClient.js"');
      import(chrome.runtime.getURL(importPath));
    })();