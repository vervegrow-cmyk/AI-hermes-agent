/**
 * @description Retrieves a key from Chrome Storage
 * @param {string} key Key to retrieve
 * @return {object} Promise => Local tools object
 */
export async function get(key) {
	return new Promise((resolve) => {
		chrome.storage.local.get([key], (result) => {
			if (!result.localSettings) {
				resolve({});
			} else {
				resolve(result.localSettings);
			}
		});
	});
}

/**
 * @description Stores a key to Chrome Storage
 * @param {string} key Ket to store
 * @param {object} value Value to save
 * @return {object} Promise => it's done
 */
export async function set(key, value) {
	return new Promise((resolve) => {
		const toStore = {};
		toStore[key] = value;
		chrome.storage.local.set(toStore, () => {
			resolve();
		});
	});
}

/**
 * @description Opens the given URL in a new tab
 * @param {string} url  URL to open
 * @return {Promise} Promise it's done
 */
export async function openTab(url) {
	return new Promise((resolve) => {
		chrome.tabs.create({ 'url': url }, (tab) => {
			resolve(tab)
		});
	})
}