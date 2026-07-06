(function() {
      const importPath = /*@__PURE__*/ JSON.parse('"contentScripts/proxySearchInject.js"');
      import(chrome.runtime.getURL(importPath));
    })();