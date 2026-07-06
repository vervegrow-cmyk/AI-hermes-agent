import * as DManip from '../../../lib/DManip.mjs';
import * as common from '../../../lib/common.mjs';
import * as actions from './actions.mjs';
import * as helpers from './helpers.mjs';

export default [
	{
		event: 'pushLiveStreamEvent',
		shouldFocus: false,
		shouldBeInitiatedBefore: true,
		execute: async (e, extercomm, lastActive, eventStorage) => {
			await extercomm.respond(e.detail.correlationId, {
				success: await pushLiveStreamEvent(eventStorage, e.detail.content, lastActive)
			});
		}
	}
];

/**
 * @description Adds a new event to livestream events
 * @param {Array} eventStorage EventStorage array to store events
 * @param {object} debugWrapper Received debug message
 * @param {object} lastActive LastActive object reference
 */
async function pushLiveStreamEvent(eventStorage, debugWrapper, lastActive) {
	// Prepare index and store
	let dontAppend = false;
	const newIndex = eventStorage.length;
	const eventView = document.getElementById('livestreamEvents');
	const debugMessage = debugWrapper.payload;
	debugMessage._engineData = {
		calledAt: debugWrapper.calledAt || 'Not available'
	}
	eventStorage.push(debugMessage);
	const bubbleStylePrebuilt = debugWrapper.module ? `background-color: ${debugWrapper.theme}` : 'display: none;';
	const eventItem = DManip.createElement('li', ['list-group-item', lastActive.odd ? 'odd' : 'even'],
		`<div class="module-bubble ${(debugWrapper.module >= 100) ? 'very-condensed' : ''}" style="${bubbleStylePrebuilt}">${debugWrapper.module}</div>
		<div class="pl-2 font-weight-bold">${debugMessage.type.charAt(0).toUpperCase() + debugMessage.type.slice(1)}</div>`);
	eventItem.setAttribute('id', `liveStereamEvent${newIndex}`);
	let haystack = '';
	try {
		haystack = JSON.stringify(debugMessage);
	} catch (err) {
		haystack = debugMessage;
	}
	haystack = common.escapeHtml(haystack);
	// Switch based on event type
	switch (debugMessage.type) {
		case 'request':
			eventItem.innerHTML += `
			<div class="pl-3 font-italic text-secondary text-truncate">
				${debugMessage.url}
			</div>
			<div class="pr-2 ml-auto">
				<span class="event-status-icon">
					<i class="fas fa-fw fa-hourglass-half"></i>
				</span>
			</div>
			`;
			eventItem.appendChild(DManip.createElement('span', ['event-search-fulltext'], `${haystack}`));
			lastActive.request = eventItem;
			lastActive.requestDataIndex = newIndex;
			lastActive.hasResponded = false;
			debugMessage.response = false;
			break;
		case 'query':
			eventItem.innerHTML += `
			<div class="pl-3 font-italic text-secondary text-truncate">
				${debugMessage.command}
			</div>
			<div class="pr-2 ml-auto">
				<span class="event-status-icon">
					<i class="fas fa-fw fa-hourglass-half"></i>
				</span>
			</div>
			`;
			eventItem.appendChild(DManip.createElement('span', ['event-search-fulltext'], `${haystack}`));
			lastActive.request = eventItem;
			lastActive.requestDataIndex = newIndex;
			lastActive.hasResponded = false;
			debugMessage.response = false;
			break;
		case 'response':
			if (lastActive.request && !lastActive.hasResponded) {
				dontAppend = true;
				lastActive.hasResponded = true;
				eventStorage[lastActive.requestDataIndex].response = debugMessage;
				lastActive.request.getElementsByClassName('event-search-fulltext')[0].innerHTML += common.escapeHtml(haystack);
				if (lastActive.event === lastActive.request) {
					const lastId = ((document
						.getElementById('livestreamDetails'))
						.querySelector('.nav-link.active')).id;
					actions.showEventDetail(eventStorage[lastActive.requestDataIndex], lastActive.requestDataIndex);
					$(`#${lastId}`).tab('show');
					window.mirrorify();
				}
				const statusIcon = lastActive.request.getElementsByClassName('event-status-icon')[0];
				if (debugMessage.status < 400) {
					statusIcon.innerHTML = `<i class="fas fa-fw fa-check-circle success"></i>`;
				} else {
					statusIcon.innerHTML = `<i class="fas fa-fw fa-exclamation-triangle error"></i>`;
				}
			} else {
				eventItem.innerHTML += `
				<div class="pl-3 font-italic text-secondary text-truncate">
					Response without preceding request
				</div>
				<div class="pr-2 ml-auto">
					<span class="event-status-icon">
						<i class="fas fa-fw fa-exclamation-triangle warning"></i>
					</span>
				</div>
				`;
				eventItem.appendChild(DManip.createElement('span', ['event-search-fulltext'], `${haystack}`));
				lastActive.request = eventItem;
				lastActive.requestDataIndex = newIndex;
				debugMessage.response = debugMessage;
			}
			break;
		case 'result':
			if (lastActive.request && !lastActive.hasResponded) {
				dontAppend = true;
				lastActive.hasResponded = true;
				eventStorage[lastActive.requestDataIndex].response = debugMessage;
				lastActive.request.getElementsByClassName('event-search-fulltext')[0].innerHTML += common.escapeHtml(haystack);
				if (lastActive.event === lastActive.request) {
					const lastId = ((document
						.getElementById('livestreamDetails'))
						.querySelector('.nav-link.active')).id;
					actions.showEventDetail(eventStorage[lastActive.requestDataIndex], lastActive.requestDataIndex);
					$(`#${lastId}`).tab('show');
					window.mirrorify();
				}
				const statusIcon = lastActive.request.getElementsByClassName('event-status-icon')[0];
				if (debugMessage.code === "0") {
					statusIcon.innerHTML = `<i class="fas fa-fw fa-check-circle success"></i>`;
				} else {
					statusIcon.innerHTML = `<i class="fas fa-fw fa-exclamation-triangle error"></i>`;
				}
			} else {
				eventItem.innerHTML += `
				<div class="pl-3 font-italic text-secondary text-truncate">
					Result without preceding query
				</div>
				<div class="pr-2 ml-auto">
					<span class="event-status-icon">
						<i class="fas fa-fw fa-exclamation-triangle warning"></i>
					</span>
				</div>
				`;
				eventItem.appendChild(DManip.createElement('span', ['event-search-fulltext'], `${haystack}`));
				lastActive.request = eventItem;
				lastActive.requestDataIndex = newIndex;
				debugMessage.response = debugMessage;
			}
			break;
		case 'message':
			eventItem.innerHTML += `
			<div class="pl-3 font-italic text-secondary text-truncate">
				${common.escapeHtml(debugMessage.args.join(', '))}
			</div>`;
			eventItem.appendChild(DManip.createElement('span', ['event-search-fulltext'], `${haystack}`));
			break;
		case 'profile':
			eventItem.innerHTML += `
			<div class="pl-3 font-italic text-secondary text-truncate">
				${debugMessage.name}, ${debugMessage.duration} ms
			</div>`;
			eventItem.appendChild(DManip.createElement('span',
				['event-search-fulltext'], `${haystack}`));
			break;
		case 'error':
			if (debugMessage.error) {
				eventItem.innerHTML += `
				<div class="pl-3 font-italic text-secondary text-truncate">
					${debugMessage.error.name} - ${debugMessage.error.message}
				</div>`;
				eventItem.appendChild(DManip.createElement('span',
					['event-search-fulltext'], `${haystack}`));
				break;
			} else {
				eventItem.innerHTML += `
				<div class="pl-3 font-italic text-secondary text-truncate">
					General Error
				</div>`;
				eventItem.appendChild(DManip.createElement('span', ['event-search-fulltext'], `${haystack}`));
				break;
			}
	}
	if (newIndex === 0) {
		eventView.innerHTML = '';
	}
	// Click activated events
	eventItem.addEventListener('click', () => {
		actions.showEventDetail(debugMessage, newIndex);
		window.mirrorify();
	});
	eventItem.addEventListener('click', () => {
		lastActive.event = helpers.highlight(eventItem, lastActive.event);
	});
	if (!dontAppend) {
		eventView.appendChild(eventItem);
		helpers.scrollIntoView(eventItem);
		lastActive.odd = !lastActive.odd;
	}
	// Return true, this will be send as a response
	return true;
}
