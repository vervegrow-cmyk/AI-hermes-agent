//监控消息发送
if (typeof origOpen == "undefined") {
  var origOpen = XMLHttpRequest.prototype.open;
}
XMLHttpRequest.prototype.open = function () {
  this.addEventListener("load", function (e) {
    try {
      let responseText = JSON.parse(this.responseText);
      if (
        (this.responseURL.indexOf("api.bilibili.com/x/player/wbi/v2") != -1 &&
          location.href.includes("bilibili.com/video")) ||
        (this.responseURL.indexOf("api.bilibili.com/x/player/wbi/v2") != -1 &&
          location.href.includes("play/"))
      ) {
        // console.log("在视频播放页");
        if (location.href.includes("play/")) {
          let arr = this.responseURL.split("?")[1].split("&");
          for (let i = 0; i < arr.length; i++) {
            // if fan
            if (arr[i].indexOf("ep_id") != -1) {
              let ep_id = arr[i].split("=")[1];
              // console.log(ep_id);
              window.postMessage(
                {
                  cmd: "XMLHttpRequestContentBiLiFan",
                  ep_id: ep_id,
                },
                "*"
              );
            }
          }
        }

        if (location.href.includes("bilibili.com/video")) {
          window.postMessage(
            {
              cmd: "XMLHttpRequestContentBiLi",
              cid: responseText.data.cid,
              bvid: responseText.data.bvid,
            },
            "*"
          );
        }
      }

      if (
        responseText.request &&
        responseText.request.files &&
        responseText.cdn_url &&
        responseText.cdn_url.indexOf("vimeo") != -1 &&
        !document.querySelector(".variant-v2")
      ) {
        if (!document.querySelector(".videoVimeoConfigUrl")) {
          document.body.insertAdjacentHTML(
            "beforeend",
            `<div class="videoVimeoConfigUrl" url=${e.currentTarget.responseURL}></div>`
          );
        } else {
          document
            .querySelector(".videoVimeoConfigUrl")
            .setAttribute("url", `${e.currentTarget.responseURL}`);
        }
      }

      if (
        this.responseURL.indexOf("https://i.instagram.com/api/v1/media") != -1
      ) {
        window.postMessage(
          {
            cmd: "XMLHttpRequestContenIns",
            responseText: responseText,
          },
          "*"
        );
      } else if (
        this.responseURL.indexOf("https://www.instagram.com/api/v1/media") != -1
      ) {
        window.postMessage(
          {
            cmd: "XMLHttpRequestContenIns",
            responseText: responseText,
          },
          "*"
        );
      } else if (
        this.responseURL.indexOf("https://www.instagram.com/api/graphql") != -1
      ) {
        window.postMessage(
          {
            cmd: "XMLHttpRequestContenIns",
            responseText: responseText,
          },
          "*"
        );
      }
    } catch (e) { }
  });
  origOpen.apply(this, arguments);
};

// 监听fetch请求
if (typeof originalFetch === "undefined") {
  var originalFetch = window.fetch;
}

window.fetch = function (url, options) {
  // 调用原始的 fetch 函数
  originalFetch(url, options)
    .then((response) => {
      return response.json();
    })
    .then((res) => {
      if (
        res.request &&
        res.request.files &&
        res.cdn_url &&
        res.cdn_url.indexOf("vimeo") != -1 &&
        !document.querySelector(".variant-v2")
      ) {
        if (!document.querySelector(".videoVimeoConfigUrl")) {
          document.body.insertAdjacentHTML(
            "beforeend",
            `<div class="videoVimeoConfigUrl" url=${url}></div>`
          );
        }
      }
    });
  return originalFetch(url, options);
};
