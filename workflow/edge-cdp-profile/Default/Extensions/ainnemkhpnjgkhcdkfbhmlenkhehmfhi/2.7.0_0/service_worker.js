let ports = 0;
chrome.runtime.onConnect.addListener((port) => {
	if (port.name === 'imt.devtool') {
		ports++;
		port.onDisconnect.addListener(() => {
			ports--;
		});
	}
});
