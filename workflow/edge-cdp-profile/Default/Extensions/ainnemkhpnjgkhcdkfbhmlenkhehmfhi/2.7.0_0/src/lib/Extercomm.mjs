/**
 * Sleeps for the given amount of milliseconds and then resolves
 * @param t {number} Timeout in milliseconds
 * @param a {T} Argument to resolve with
 * @return Promise<T>
 */
const sleep = async (t, a) => new Promise(r => setTimeout(_ => r(a), t));

class Extercomm extends EventTarget {

	/**
	 * @description A constructor of the Extercomm
	 */
	constructor() {
		super();
		this.resolver = {};
		this.connected = false;
		this.connectionId = undefined;
	}

	/**
	 * @description Asynchronous initialization of the Extercomm, which will inject the message transciever into the host page
	 * @param {object} settings Settings to send
	 */
	async init(settings) {
		this.cid = this.generateUUID();
		await new Promise((resolve) => {
			chrome.scripting.executeScript({
				target: {tabId: chrome.devtools.inspectedWindow.tabId},
				func: (cid) => {
					document.addEventListener("imt-extercomm-wte-request", function(e) {
						chrome.runtime.sendMessage(JSON.stringify({type: e.type, detail: e.detail, cid})); });
					document.addEventListener("imt-extercomm-wte-response", function(e) {
						chrome.runtime.sendMessage(JSON.stringify({type: e.type, detail: e.detail, cid})); });
				},
				args: [ this.cid ]
			}).then(resolve());
		});

		chrome.runtime.onMessage.addListener((message) => {
			const e = JSON.parse(message);
			if (e.cid !== this.cid) {
				return;
			}
			switch (e.type) {
				case 'imt-extercomm-wte-request':
					this.dispatchEvent(new CustomEvent(e.detail.event, {
						detail: {
							content: e.detail.content,
							correlationId: e.detail.correlationId
						}
					}));
					break;
				case 'imt-extercomm-wte-response':
					if (!this.resolver[e.detail.correlationId]) {
						console.warn(`No handler kept for ${e.detail.correlationId}. Response void.`);
						break;
					}
					if (e.detail.error) {
						this.resolver[e.detail.correlationId].reject(e.detail.error);
					} else {
						this.resolver[e.detail.correlationId].resolve(e.detail.content);
					}
					break;
				default:
					console.warn('Unexpected event type received.');
			}
		});

		// Try connecting to the Host
		const timeout = 500;
		const attempt = async () => {
			const response = await Promise.race([
				this.send('greetings', { cid: this.cid, settings: settings }),
				sleep(timeout, false)
			]);
			if (response === false) {
				return false;
			}
			if (!response.hello) {
				console.error(`Greeting failed.`);
			} else {
				this.connected = true;
				this.webSettings = response.settings;
			}
			return true;
		};

		let attemptsLeft = 6;
		do {
			console.log(`Connecting to Extercomm...`);
			const attemptResult = await attempt();
			if (attemptResult === true) {
				console.log(`Extercomm conncted!`);
				return true;
			}
			await sleep(timeout);
		} while(--attemptsLeft);
		return false;
	}

	/**
	 * @description Sends a new event to the host page
	 * @param {string} eventType Type of the event which will be emitted on the other side
	 * @param {object} content JSON serializable object. A copy will be passed, no references are available
	 * @return {Promise} A new Promise which will be resolved with response from the host page
	 */
	async send(eventType, content) {
		return new Promise(async (resolve, reject) => {
			const uuid = this.generateUUID();
			const request = { event: eventType, content: content, correlationId: uuid };
			this.resolver[uuid] = {
				resolve: resolve,
				reject: reject
			};
			await this.evaluate(`
			document.dispatchEvent(new CustomEvent('imt-extercomm-etw-request', { 
				detail: ${JSON.stringify(request)} 
			}));`);
		});
	}

	/**
	 * @description Sends a response to the host page
	 * @param {string} correlationId Correlation UUID obtained from request. Will resolve the waiting promise on the requester
	 * @param {object} content JSON serializable object. A copy will be passed, no references are available
	 */
	async respond(correlationId, content) {
		const response = { content: content, correlationId: correlationId };
		await this.evaluate(`
		document.dispatchEvent(new CustomEvent('imt-extercomm-etw-response', { 
			detail: ${JSON.stringify(response)} 
		}));`);
	}

	/**
	 * @description Evaluates the code in the host page
	 * @param {string} code A code to evaluate
	 * @param {object} options Evaluation options
	 * @return {Promise} Promise which will get resolved when the code is evaluated
	 */
	async evaluate(code, options) {
		return await new Promise((resolve) => {
			chrome.devtools.inspectedWindow.eval(
				code, options, (res) => {
					resolve(res);
				}
			);
		});
	}

	/**
	 * @description Generates new UUID string
	 * @return {string} New UUID string
	 */
	generateUUID() {
		let dt = new Date().getTime();
		const uuid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
			const r = (dt + Math.random() * 16) % 16 | 0;
			dt = Math.floor(dt / 16);
			return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
		});
		return uuid;
	}

}

export default Extercomm;
