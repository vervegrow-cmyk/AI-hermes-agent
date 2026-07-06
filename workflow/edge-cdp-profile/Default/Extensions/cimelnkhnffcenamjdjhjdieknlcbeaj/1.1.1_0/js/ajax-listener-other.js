//监控消息发送
if (!location.href.includes('vimeo.com') && !location.href.includes('tiktok.com') && !location.href.includes('dailymotion.com')
	&& !location.href.includes('twitch.tv') && !location.href.includes('pinterest.com') && !location.href.includes('facebook.com')
	&& !location.href.includes('bilibili.com') && !location.href.includes('instagram.com') && !location.href.includes('reddit.com')
	&& !location.href.includes('twitter.com') && !location.href.includes('youtube.com')) {
	// XHR
	if (typeof origOpen == "undefined") {
		var origOpen = XMLHttpRequest.prototype.open;
	}
	XMLHttpRequest.prototype.open = function () {
		this.addEventListener("load", function (e) {
			if (this.responseURL.indexOf(".m3u8") != -1 && this.responseText) {
				window.postMessage(
					{
						cmd: "getM3U8",
						url: this.responseURL,
						size: this.getResponseHeader("Content-Length"),
						m3u8Text: this.responseText
					},
					"*"
				);
			}
		});
		origOpen.apply(this, arguments);
	};

	// fetch
	//   function onFetch(callback) {
	//     // let logFetch = window.fetch
	//     window.fetch = function (input, init) {
	//         if (input.includes('.m3u8')) {
	//           console.log(input, init, this.getResponseHeader("Content-Length"))
	//           window.postMessage(
	//               {
	//                 cmd: "getM3U8",
	//                 url: input,
	//                 size: this.getResponseHeader("Content-Length")
	//               },
	//               "*"
	//           );
	//         }
	//     }
	//   }
	//   onFetch(response => {
	//     response.json()
	//     .then(res=>{
	// 		console.log(res)
	// 	})
	// })

}
