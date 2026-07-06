// (function (xhr) {

//   var XHR = XMLHttpRequest.prototype;

//   var open = XHR.open;
//   var send = XHR.send;

//   XHR.open = function (method, url) {
//       this._method = method;
//       this._url = url;
//       return open.apply(this, arguments);
//   };

//   XHR.send = function (postData) {
//       this.addEventListener('load', function () {
//           if (this._url && this._url.includes('youtube.com/api/timedtext')) {
//             window.postMessage({ type: 'xhr', name: 'timedtext', data: this.response }, '*');  // send to content script
//           }
//       });
//       return send.apply(this, arguments);
//   };
// })(XMLHttpRequest);

// const { fetch: origFetch } = window;
// window.fetch = async (...args) => {
//   const response = await origFetch(...args);
//   let url = '';
//   if (args.length && args[0] && args[0].url) {
//     url = args[0].url;
//   }

//   if (url && url.includes('youtube.com/youtubei/v1/next')) {
//     response
//       .clone()
//       .json() // maybe json(), text(), blob()
//       .then(data => {
//         window.postMessage({ type: 'fetch', name: 'comment', data: data }, '*');  // send to content script
//         //window.postMessage({ type: 'fetch', data: URL.createObjectURL(data) }, '*'); // if a big media file, can createObjectURL before send to content script
//       })
//       .catch(err => console.error(err));
//   }
//   return response;
// };
if (origin === 'https://partner.us.tiktokshop.com') {
  window.postMessage(JSON.stringify({
    app_id: window.__TTSPC_APP_ENVS__?.app_id,
    type: 'PBTransferAccountInfoParam',
  }), '*');
} else {
  window.postMessage({ type: 'getWindowData', name: 'accountInfoParam', data: window._accountInfoParam }, '*');
}

(function () {
  var ALIYUN_CAPTCHA_SCRIPT_SRC = 'https://o.alicdn.com/captcha-frontend/aliyunCaptcha/AliyunCaptcha.js';
  var scriptPromise = null;
  var initPromise = null;
  var captchaInstance = null;
  var pendingRequest = null;

  function emitResult(requestId, payload) {
    window.dispatchEvent(new CustomEvent('PB_ALIYUN_CAPTCHA_RESULT', {
      detail: Object.assign({ requestId: requestId }, payload)
    }));
  }

  function resetCaptcha() {
    var instance = captchaInstance;
    captchaInstance = null;
    initPromise = null;
    pendingRequest = null;

    if (instance) {
      try {
        instance.hide && instance.hide();
        instance.reset && instance.reset();
        instance.reload && instance.reload();
        instance.destroy && instance.destroy();
      } catch (error) {
        console.warn('Aliyun captcha reset failed', error);
      }
    }

    var element = document.getElementById('aliyun-captcha-element');
    if (element) {
      element.replaceChildren();
    }
  }

  function loadScript(config) {
    if (window.initAliyunCaptcha) return Promise.resolve();
    if (scriptPromise) return scriptPromise;

    window.AliyunCaptchaConfig = {
      region: config.region,
      prefix: config.prefix,
    };

    scriptPromise = new Promise(function (resolve, reject) {
      var existingScript = document.querySelector('script[src="' + ALIYUN_CAPTCHA_SCRIPT_SRC + '"]');
      if (existingScript) {
        existingScript.remove();
      }

      var script = document.createElement('script');
      script.type = 'text/javascript';
      script.src = ALIYUN_CAPTCHA_SCRIPT_SRC;
      script.async = true;
      script.onload = function () {
        if (!window.initAliyunCaptcha) {
          scriptPromise = null;
          reject(new Error('验证码初始化方法不存在'));
          return;
        }
        resolve();
      };
      script.onerror = function () {
        scriptPromise = null;
        script.remove();
        reject(new Error('验证码脚本加载失败'));
      };
      document.head.appendChild(script);
    });

    return scriptPromise;
  }

  function initCaptcha(request) {
    if (captchaInstance) return Promise.resolve();
    if (initPromise) return initPromise;

    initPromise = new Promise(function (resolve, reject) {
      var settled = false;
      var initTimer = null;

      function resolveInit() {
        if (settled) return;
        settled = true;
        if (initTimer !== null) {
          window.clearTimeout(initTimer);
        }
        resolve();
      }

      function rejectInit(error) {
        if (settled) return;
        settled = true;
        initPromise = null;
        if (initTimer !== null) {
          window.clearTimeout(initTimer);
        }
        reject(error);
      }

      loadScript(request.config)
        .then(function () {
          if (!window.initAliyunCaptcha) {
            throw new Error('验证码初始化方法不存在');
          }

          initTimer = window.setTimeout(function () {
            rejectInit(new Error('验证码初始化超时'));
          }, 10000);

          window.initAliyunCaptcha({
            SceneId: request.config.sceneId,
            mode: 'popup',
            element: request.element,
            button: request.button,
            success: function (captchaVerifyParam) {
              if (!pendingRequest) return;
              var current = pendingRequest;
              emitResult(current.requestId, {
                status: 'success',
                captchaVerifyParam: captchaVerifyParam,
              });
              resetCaptcha();
            },
            fail: function (result) {
              console.warn('Aliyun captcha verification failed', result);
            },
            onError: function (errorInfo) {
              var message = (errorInfo && errorInfo.msg) || '验证码加载失败，请稍后重试';
              var current = pendingRequest || request;
              emitResult(current.requestId, {
                status: 'abnormal',
                message: message,
              });
              resetCaptcha();
              rejectInit(new Error(message));
            },
            onClose: function () {
              if (!pendingRequest) return;
              var current = pendingRequest;
              emitResult(current.requestId, {
                status: 'cancelled',
                message: '已取消验证码验证',
              });
              resetCaptcha();
            },
            getInstance: function (instance) {
              captchaInstance = instance;
              resolveInit();
            },
            language: 'cn',
            timeout: 5000,
          });
        })
        .catch(function (error) {
          rejectInit(error);
        });
    });

    return initPromise;
  }

  window.addEventListener('PB_ALIYUN_CAPTCHA_RESET', resetCaptcha);

  window.addEventListener('PB_ALIYUN_CAPTCHA_REQUEST', function (event) {
    var request = event.detail;
    if (!request || !request.requestId || !request.config) return;

    initCaptcha(request)
      .then(function () {
        if (request.type === 'prepare') {
          emitResult(request.requestId, { status: 'prepared' });
          return;
        }

        pendingRequest = request;
        if (captchaInstance && captchaInstance.show) {
          captchaInstance.show();
          return;
        }

        var trigger = document.querySelector(request.button);
        trigger && trigger.click();
      })
      .catch(function (error) {
        emitResult(request.requestId, {
          status: 'abnormal',
          message: error && error.message,
        });
        resetCaptcha();
      });
  });
})();
