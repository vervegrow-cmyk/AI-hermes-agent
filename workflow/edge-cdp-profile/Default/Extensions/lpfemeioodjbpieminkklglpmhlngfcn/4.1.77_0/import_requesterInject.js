(function() {
      const importPath = /*@__PURE__*/ JSON.parse('"contentScripts/requesterInject.js"');
      import(chrome.runtime.getURL(importPath));
    })();