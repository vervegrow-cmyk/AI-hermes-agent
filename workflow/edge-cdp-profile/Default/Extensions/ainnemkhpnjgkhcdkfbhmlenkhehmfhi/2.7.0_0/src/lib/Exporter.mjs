/**
 * @description Generates a cURL script representing the request
 * @param {object} raw Raw request-response object
 * @return {string} cURL run-ready command
 */
export function generateCURL(raw) {
	let out = `curl -X ${raw.method.toUpperCase()} '${raw.url}`;
	if (raw.qs) {
		out += '?';
		out += Object.keys(raw.qs).map(k => `${k}=${encodeURI(raw.qs[k])}`).join('&');
	}
	out += `'`;
	if (raw.headers) {
		Object.keys(raw.headers).forEach(k => {
			out += ` -H '${k}: ${raw.headers[k]}'`;
		});
	}
	if (raw.body) {
		if (raw.body instanceof Object) {
			out += ` -d '${JSON.stringify(raw.body)}'`;
		} else {
			out += ` -d '${raw.body}'`;
		}
	}
	return out;
}

/**
 * @description Generates full request-response report from the object
 * @param {object} e Request-response object
 * @return {string} Stringified request-response log in human readable format (mostly)
 */
export function generateRawReport(e) {
	const c = Object.assign({}, e);
	c.request = {
		url: c.url,
		qs: c.qs,
		headers: c.headers,
		method: c.method,
		body: c.body
	};
	delete c.url;
	delete c.type;
	delete c.qs;
	delete c.headers;
	delete c.method;
	delete c.body;
	if (c.response) {
		delete c.response.type;
		try {
			c.response.body = JSON.parse(c.response.body);
		} catch (err) {

		}
	}
	try {
		c.request.body = JSON.parse(c.request.body);
	} catch (err) {

	}
	return JSON.stringify(c, null, 4);
}

/**
 * @description A string to be copiped to clipboard
 * @param {string} str String to be copied to cpliboard
 */
export function copyStringToClipboard(str) {
	const el = document.createElement('textarea');
	el.value = str;
	el.setAttribute('readonly', '');
	el.style = { position: 'absolute', left: '-9999px' };
	document.body.appendChild(el);
	el.select();
	document.execCommand('copy');
	document.body.removeChild(el);
}
