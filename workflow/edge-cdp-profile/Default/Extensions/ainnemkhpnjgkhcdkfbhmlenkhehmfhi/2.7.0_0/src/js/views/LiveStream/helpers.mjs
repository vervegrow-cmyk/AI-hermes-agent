/**
 * @description Clears all panes
 */
export function clearPanes() {
	const eventView = document.getElementById('livestreamEvents');
	const eventDetailView = document.getElementById('livestreamDetails');
	eventView.innerHTML = '<li class="my-auto text-center font-weight-bold text-secondary lead">No events available</li>';
	eventDetailView.innerHTML = `
	<div class="card-body d-flex text-center font-weight-bold text-secondary lead">
		<p class="my-auto mx-auto"> No event selected</p>
	</div>`;
}
/**
 * @description Event Search utility
 */
export function eventSearch() {
	const query = (document.getElementById('livestreamEventsSearch').value).toLowerCase();
	const scope = document.getElementsByClassName('event-search-fulltext');
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
export async function unfocusEvent(lastActive) {
	setPanes([
		{
			id: 'livestreamDetails',
			html: '<div class="card-body d-flex text-center font-weight-bold text-secondary lead"><p class="my-auto mx-auto">No event selected</p></div>'
		}
	]);
	if (lastActive && lastActive.event) {
		lastActive.event.classList.remove(`active`);
	}
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
