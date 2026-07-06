var background = (function() {
	//#region ../../node_modules/wxt/dist/utils/define-background.mjs
	function defineBackground(arg) {
		if (arg == null || typeof arg === "function") return { main: arg };
		return arg;
	}
	//#endregion
	//#region src/agent/RemotePageController.background.ts
	/**
	* background logics for RemotePageController
	* - redirect messages from RemotePageController(Agent, extension pages) to ContentScript
	*/
	function handlePageControlMessage(message, sender, sendResponse) {
		const PREFIX = "[RemotePageController.background]";
		const debug = console.debug.bind(console, `\x1b[90m${PREFIX}\x1b[0m`);
		const { action, payload, targetTabId } = message;
		if (action === "get_my_tab_id") {
			debug("get_my_tab_id", sender.tab?.id);
			sendResponse({ tabId: sender.tab?.id || null });
			return;
		}
		chrome.tabs.sendMessage(targetTabId, {
			type: "PAGE_CONTROL",
			action,
			payload
		}).then((result) => {
			sendResponse(result);
		}).catch((error) => {
			console.error(PREFIX, error);
			sendResponse({
				success: false,
				error: error instanceof Error ? error.message : String(error)
			});
		});
		return true;
	}
	//#endregion
	//#region src/agent/TabsController.background.ts
	var PREFIX = "[TabsController.background]";
	var debug = console.debug.bind(console, `\x1b[90m${PREFIX}\x1b[0m`);
	/**
	* Resolve active tab.
	*
	* - `tabs.query({ active: true })` does not work in multi-window scenarios.
	* - Extension pages (side panel, hub tab) can resolve their own windowId.
	*   We just find the active tab within that window.
	* - Content scripts (PAGE_AGENT_EXT) can't self-report a windowId.
	*   Chrome populates `sender.tab` for every content-script message,
	*   which is the tab hosting the script.
	*/
	async function resolveActiveTab(payload, sender) {
		const windowId = payload?.windowId;
		if (windowId != null) {
			debug("get_active_tab: resolving via caller-reported windowId", windowId);
			const [tab] = await chrome.tabs.query({
				active: true,
				windowId
			});
			if (!tab) throw new Error(`No active tab found in window ${windowId}.`);
			return tab;
		}
		if (sender.tab) {
			debug("get_active_tab: resolving via sender.tab (content script)", sender.tab.id);
			return sender.tab;
		}
		throw new Error("Cannot resolve active tab: caller reported no windowId and is not a content script (no sender.tab).");
	}
	function handleTabControlMessage(message, sender, sendResponse) {
		const { action, payload } = message;
		switch (action) {
			case "get_active_tab":
				debug("get_active_tab", payload);
				resolveActiveTab(payload, sender).then((tab) => {
					debug("get_active_tab: success", tab);
					sendResponse({
						success: true,
						tab
					});
				}).catch((error) => {
					sendResponse({ error: error instanceof Error ? error.message : String(error) });
				});
				return true;
			case "get_tab_info":
				debug("get_tab_info", payload);
				chrome.tabs.get(payload.tabId).then((tab) => {
					debug("get_tab_info: success", tab);
					sendResponse(tab);
				}).catch((error) => {
					sendResponse({ error: error instanceof Error ? error.message : String(error) });
				});
				return true;
			case "open_new_tab":
				debug("open_new_tab", payload);
				chrome.tabs.create({
					url: payload.url,
					windowId: payload.windowId,
					active: false
				}).then((newTab) => {
					debug("open_new_tab: success", newTab);
					sendResponse({
						success: true,
						tabId: newTab.id
					});
				}).catch((error) => {
					sendResponse({ error: error instanceof Error ? error.message : String(error) });
				});
				return true;
			case "create_tab_group":
				debug("create_tab_group", payload);
				chrome.tabs.group({
					tabIds: payload.tabIds,
					createProperties: { windowId: payload.windowId }
				}).then((groupId) => {
					debug("create_tab_group: success", groupId);
					sendResponse({
						success: true,
						groupId
					});
				}).catch((error) => {
					console.error(PREFIX, "Failed to create tab group", error);
					sendResponse({ error: error instanceof Error ? error.message : String(error) });
				});
				return true;
			case "update_tab_group":
				debug("update_tab_group", payload);
				chrome.tabGroups.update(payload.groupId, payload.properties).then(() => {
					sendResponse({ success: true });
				}).catch((error) => {
					sendResponse({ error: error instanceof Error ? error.message : String(error) });
				});
				return true;
			case "add_tab_to_group":
				debug("add_tab_to_group", payload);
				chrome.tabs.group({
					tabIds: payload.tabId,
					groupId: payload.groupId
				}).then(() => {
					sendResponse({ success: true });
				}).catch((error) => {
					sendResponse({ error: error instanceof Error ? error.message : String(error) });
				});
				return true;
			case "close_tab":
				debug("close_tab", payload);
				chrome.tabs.remove(payload.tabId).then(() => {
					sendResponse({ success: true });
				}).catch((error) => {
					sendResponse({ error: error instanceof Error ? error.message : String(error) });
				});
				return true;
			case "get_window_tabs":
				debug("get_window_tabs", payload);
				chrome.tabs.query({ windowId: payload.windowId }).then((tabs) => {
					sendResponse({
						success: true,
						tabs
					});
				}).catch((error) => {
					sendResponse({ error: error instanceof Error ? error.message : String(error) });
				});
				return true;
			default:
				sendResponse({ error: `Unknown action: ${action}` });
				return;
		}
	}
	var tabEventPorts = /* @__PURE__ */ new Set();
	function broadcastTabEvent(message) {
		for (const port of tabEventPorts) port.postMessage(message);
	}
	/**
	* Port-based tab events: agents connect via `chrome.runtime.connect({ name: 'tab-events' })`
	* and receive tab change events through the port. Works for both extension pages and content scripts.
	*/
	function setupTabEventsPort() {
		chrome.runtime.onConnect.addListener((port) => {
			if (port.name !== "tab-events") return;
			debug("port connected", port.sender?.tab?.id ?? port.sender?.url);
			tabEventPorts.add(port);
			port.onDisconnect.addListener(() => {
				debug("port disconnected");
				tabEventPorts.delete(port);
			});
		});
		chrome.tabs.onCreated.addListener((tab) => {
			broadcastTabEvent({
				action: "created",
				payload: { tab }
			});
		});
		chrome.tabs.onRemoved.addListener((tabId, removeInfo) => {
			broadcastTabEvent({
				action: "removed",
				payload: {
					tabId,
					removeInfo
				}
			});
		});
		chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
			broadcastTabEvent({
				action: "updated",
				payload: {
					tabId,
					changeInfo,
					tab
				}
			});
		});
	}
	//#endregion
	//#region src/entrypoints/background.ts
	var background_default = defineBackground(() => {
		console.log("[Background] Service Worker started");
		setupTabEventsPort();
		chrome.storage.local.get("PageAgentExtUserAuthToken").then((result) => {
			if (result.PageAgentExtUserAuthToken) return;
			const userAuthToken = crypto.randomUUID();
			chrome.storage.local.set({ PageAgentExtUserAuthToken: userAuthToken });
		});
		chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
			if (message.type === "TAB_CONTROL") return handleTabControlMessage(message, sender, sendResponse);
			else if (message.type === "PAGE_CONTROL") return handlePageControlMessage(message, sender, sendResponse);
			else {
				sendResponse({ error: "Unknown message type" });
				return;
			}
		});
		chrome.runtime.onMessageExternal.addListener((message, sender, sendResponse) => {
			if (message.type === "OPEN_HUB") {
				openOrFocusHubTab(message.wsPort).then(() => {
					if (sender.tab?.id) chrome.tabs.remove(sender.tab.id);
					sendResponse({ ok: true });
				});
				return true;
			}
		});
		chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true }).catch(() => {});
	});
	async function openOrFocusHubTab(wsPort) {
		const hubUrl = chrome.runtime.getURL("hub.html");
		const existing = await chrome.tabs.query({ url: `${hubUrl}*` });
		if (existing.length > 0 && existing[0].id) {
			await chrome.tabs.update(existing[0].id, {
				active: true,
				url: `${hubUrl}?ws=${wsPort}`
			});
			return;
		}
		await chrome.tabs.create({
			url: `${hubUrl}?ws=${wsPort}`,
			pinned: true
		});
	}
	globalThis.browser?.runtime?.id ? globalThis.browser : globalThis.chrome;
	//#endregion
	//#region ../../node_modules/@webext-core/match-patterns/lib/index.js
	var _MatchPattern = class {
		constructor(matchPattern) {
			if (matchPattern === "<all_urls>") {
				this.isAllUrls = true;
				this.protocolMatches = [..._MatchPattern.PROTOCOLS];
				this.hostnameMatch = "*";
				this.pathnameMatch = "*";
			} else {
				const groups = /(.*):\/\/(.*?)(\/.*)/.exec(matchPattern);
				if (groups == null) throw new InvalidMatchPattern(matchPattern, "Incorrect format");
				const [_, protocol, hostname, pathname] = groups;
				validateProtocol(matchPattern, protocol);
				validateHostname(matchPattern, hostname);
				this.protocolMatches = protocol === "*" ? ["http", "https"] : [protocol];
				this.hostnameMatch = hostname;
				this.pathnameMatch = pathname;
			}
		}
		includes(url) {
			if (this.isAllUrls) return true;
			const u = typeof url === "string" ? new URL(url) : url instanceof Location ? new URL(url.href) : url;
			return !!this.protocolMatches.find((protocol) => {
				if (protocol === "http") return this.isHttpMatch(u);
				if (protocol === "https") return this.isHttpsMatch(u);
				if (protocol === "file") return this.isFileMatch(u);
				if (protocol === "ftp") return this.isFtpMatch(u);
				if (protocol === "urn") return this.isUrnMatch(u);
			});
		}
		isHttpMatch(url) {
			return url.protocol === "http:" && this.isHostPathMatch(url);
		}
		isHttpsMatch(url) {
			return url.protocol === "https:" && this.isHostPathMatch(url);
		}
		isHostPathMatch(url) {
			if (!this.hostnameMatch || !this.pathnameMatch) return false;
			const hostnameMatchRegexs = [this.convertPatternToRegex(this.hostnameMatch), this.convertPatternToRegex(this.hostnameMatch.replace(/^\*\./, ""))];
			const pathnameMatchRegex = this.convertPatternToRegex(this.pathnameMatch);
			return !!hostnameMatchRegexs.find((regex) => regex.test(url.hostname)) && pathnameMatchRegex.test(url.pathname);
		}
		isFileMatch(url) {
			throw Error("Not implemented: file:// pattern matching. Open a PR to add support");
		}
		isFtpMatch(url) {
			throw Error("Not implemented: ftp:// pattern matching. Open a PR to add support");
		}
		isUrnMatch(url) {
			throw Error("Not implemented: urn:// pattern matching. Open a PR to add support");
		}
		convertPatternToRegex(pattern) {
			const starsReplaced = this.escapeForRegex(pattern).replace(/\\\*/g, ".*");
			return RegExp(`^${starsReplaced}$`);
		}
		escapeForRegex(string) {
			return string.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
		}
	};
	var MatchPattern = _MatchPattern;
	MatchPattern.PROTOCOLS = [
		"http",
		"https",
		"file",
		"ftp",
		"urn"
	];
	var InvalidMatchPattern = class extends Error {
		constructor(matchPattern, reason) {
			super(`Invalid match pattern "${matchPattern}": ${reason}`);
		}
	};
	function validateProtocol(matchPattern, protocol) {
		if (!MatchPattern.PROTOCOLS.includes(protocol) && protocol !== "*") throw new InvalidMatchPattern(matchPattern, `${protocol} not a valid protocol (${MatchPattern.PROTOCOLS.join(", ")})`);
	}
	function validateHostname(matchPattern, hostname) {
		if (hostname.includes(":")) throw new InvalidMatchPattern(matchPattern, `Hostname cannot include a port`);
		if (hostname.includes("*") && hostname.length > 1 && !hostname.startsWith("*.")) throw new InvalidMatchPattern(matchPattern, `If using a wildcard (*), it must go at the start of the hostname`);
	}
	//#endregion
	//#region \0virtual:wxt-background-entrypoint?/Users/meng/work/code/page-agent/packages/extension/src/entrypoints/background.ts
	/** Wrapper around `console` with a "[wxt]" prefix */
	var logger = {
		debug: (...args) => ([...args], void 0),
		log: (...args) => ([...args], void 0),
		warn: (...args) => ([...args], void 0),
		error: (...args) => ([...args], void 0)
	};
	var result;
	try {
		result = background_default.main();
		if (result instanceof Promise) console.warn("The background's main() function return a promise, but it must be synchronous");
	} catch (err) {
		logger.error("The background crashed on startup!");
		throw err;
	}
	//#endregion
	return result;
})();
