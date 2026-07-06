/**
 * @description Handles the module ID/Name search bar
 */
export function moduleSearch() {
	const query = (document.getElementById('moduleSearch').value).toLowerCase();
	const scope = document.getElementsByClassName('module-search-fulltext');
	for (const e of scope) {
		if (e.innerHTML.toLowerCase().indexOf(query) === -1) {
			e.parentElement.style.setProperty('display', 'none', 'important');
		} else {
			e.parentElement.style.setProperty('display', 'flex', 'important');
		}
	}
}

/**
 * @description Highlights a clicked sender
 * @param {HTMLElement} sender A sender which invoked the function
 * @param {HTMLElement} lastSender Last active entity of the same type
 * @return {HTMLElement} The sender object
 */
export function highlight(sender, lastSender) {
	if (lastSender) {
		lastSender.classList.remove(`active`);
	}
	sender.classList.add(`active`);
	return sender;
}

/**
 * @description Scrolls the element to the center of the list (or at least tries to do so)
 * @param {HTMLElement} sender A sender which invoked the function
 */
export function scrollIntoView(sender) {
	sender.scrollIntoView({
		block: 'center'
	});
}

/**
 * @description Clears content of all extension panes
 * @param {Array} panes List of panes to clear
 */
export async function setPanes(panes) {
	panes.forEach(pane => {
		document.getElementById(`${pane.id}ListItems`).innerHTML = pane.html;
	});
}

/**
 * @description Module unfocus
 * @param {object} lastActive Last active instances
 */
export async function unfocusModule(lastActive) {
	setPanes([
		{ id: 'cycle', html: '<li class="my-auto text-center font-weight-bold text-secondary lead">No module selected</li>' },
		{ id: 'event', html: '<li class="my-auto text-center font-weight-bold text-secondary lead">No operation selected</li>' }
	]);
	if (lastActive && lastActive.module) {
		lastActive.module.classList.remove(`active`);
	}
}

/**
 * @description Operation unfocus
 * @param {object} lastActive Last active instances
 */
export async function unfocusOperation(lastActive) {
	setPanes([
		{ id: 'event', html: '<li class="my-auto text-center font-weight-bold text-secondary lead">No operation selected</li>' }
	]);
	if (lastActive && lastActive.operation) {
		lastActive.operation.classList.remove(`active`);
	}
}

/**
 * @description Focuses module in webview
 * @param {Extercomm} extercomm An instance of the Extercomm to use
 * @param {Number} module ID of the module
 * @param {Number} cycle n-th cycle index
 * @param {Number} operation m-th operation index
 */
export async function focusModule(extercomm, module, cycle, operation) {
	const result = await extercomm.send('focusModule', {
		module: module,
		cycle: cycle,
		operation: operation
	});
	return result;
}