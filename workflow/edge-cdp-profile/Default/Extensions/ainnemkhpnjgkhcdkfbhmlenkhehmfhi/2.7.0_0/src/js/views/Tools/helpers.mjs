/**
 * @description Clears all panes
 */
export function clearPanes() {
	const toolsWrapper = document.getElementById('toolsRow');
	const toolWindow = document.getElementById('toolWindow');
	toolsWrapper.innerHTML = '';
	toolWindow.innerHTML = `
	<div class="fullheight d-flex text-center font-weight-bold text-secondary lead">
		<p class="my-auto mx-auto">No tool selected</p>
	</div>`;
}

/**
 * @description Tool search utility
 * @param {object} lastActive Last active entity store
 */
export function toolsSearch(lastActive) {
	const query = (document.getElementById('toolsSearch').value).toLowerCase();
	const scope = document.getElementsByClassName('tool-search-fulltext');
	for (const e of scope) {
		if (e.innerHTML.toLowerCase().indexOf(query) === -1) {
			e.parentElement.style.setProperty('display', 'none', 'important');
		} else {
			e.parentElement.style.removeProperty('display');
		}
	}
	// Blessed be the fruit...
	if (query === 'idkfa') {
		lastActive.hiddenTools.forEach(tool => {
			tool.classList.remove('d-none');
		});
	}
}

/**
 * @description Highlights a clicked sender
 * @param {HTMLElement} sender A sender which invoked the function
 * @param {string} color Color to set
 * @param {object} lastSender Last active entity store
 * @param {object} lastColor Last color
 */
export function highlight(sender, color, lastSender, lastColor) {
	if (lastSender) {

		// eslint-disable-next-line no-undef
		lastSender.style.color = new Color(lastColor).determineForegroundColor().toHex();
		lastSender.style.backgroundColor = lastColor;
		lastSender.classList.remove(`active`);
	}

	// eslint-disable-next-line no-undef
	sender.style.color = new Color(color).determineForegroundColor().toHex();
	sender.style.backgroundColor = color;
	sender.classList.add(`active`);
}

/**
 * @description Clears content of all extension panes
 * @param {Array} panes List of panes to clear
 */
export async function setPanes(panes) {
	panes.forEach(pane => {
		document.getElementById(`${pane.id}`).innerHTML = pane.html;
	});
}

/**
 * @description Event unfocus
 * @param {object} lastActive Last active instances
 */
export async function unfocusTool(lastActive) {
	setPanes([
		{
			id: 'toolWindow',
			html: '<div class="fullheight d-flex text-center font-weight-bold text-secondary lead"><p class="my-auto mx-auto">No tool selected</p></div>'
		}
	]);
	if (lastActive && lastActive.tool) {

		// eslint-disable-next-line no-undef
		lastActive.tool.style.color = new Color(lastActive.toolColor).determineForegroundColor().toHex();
		lastActive.tool.style.backgroundColor = lastActive.toolColor;
		lastActive.tool.classList.remove(`active`);
	}
}

/**
 * @description Retrieves user defined tools stored locally in Google Chrome
 * @return {object} Promise => Local tools object
 */
export async function getLocalTools() {
	return new Promise((resolve) => {
		chrome.storage.local.get(['localTools'], (result) => {
			if (!result.localTools) {
				resolve({});
			} else {
				resolve(result.localTools);
			}
		});
	});
}

/**
 * @description Stores user defined tools to Chrome local storage
 * @param {object} tools Tools object to save
 * @return {object} Promise => it's done
 */
export async function saveLocalTools(tools) {
	return new Promise((resolve) => {
		chrome.storage.local.set({ localTools: tools }, () => {
			resolve();
		});
	});
}

/**
 * @description Verifies if the admin mode is true or false
 * @param {object} extercomm Extercomm instance to user
 * @return {boolean} Admin or not, true or false
 */
export async function isAdmin(extercomm) {
	return (await extercomm.evaluate(`imt.admin`));
}
