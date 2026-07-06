import handlers from './handlers.mjs';
import * as helpers from './helpers.mjs';
import * as ChromeAsync from '../../../lib/ChromeAsync.mjs';

import { default as template } from './template.mjs';
export const config = {
	id: 'liveStream',
	name: 'Live Stream',
	sidebarIcon: ['far', 'fa-fw', 'fa-shipping-fast'],
	template: template
};

// Event Storage stores all received events
// LastActive holds last clicked event
let eventStorage = [];
const lastActive = {
	event: null,
	request: undefined,
	requestDataIndex: undefined,
	odd: true
};

/**
 * Main initializer function
 * @param {extercomm} extercomm Extercomm instance to use
 */
export async function init(extercomm) {
	lastActive.localSettings = await ChromeAsync.get('localSettings');
	if (lastActive.localSettings.console) {
		document.getElementById('livestreamToggleConsole').classList.add('searchbar-action-enabled');
	}
	document.getElementById('livestreamEventsSearch').addEventListener('keyup', helpers.eventSearch);
	document.getElementById('livestreamOpenHelp').addEventListener('click', async () => {
		await ChromeAsync.openTab(`https://www.make.com/en/help/scenarios/make-devtool#using-live-stream`);
	});
	document.getElementById('livestreamClearEvents').addEventListener('click', () => {
		helpers.clearPanes();
		eventStorage = [];
	});
	document.getElementById('livestreamToggleConsole').addEventListener('click', async () => {
		lastActive.localSettings.console = !lastActive.localSettings.console;
		if (lastActive.localSettings.console) {
			document.getElementById('livestreamToggleConsole').classList.add('searchbar-action-enabled');
		} else {
			document.getElementById('livestreamToggleConsole').classList.remove('searchbar-action-enabled');
		}
		await extercomm.send('updateSettings', { console: lastActive.localSettings.console });
		await ChromeAsync.set('localSettings', lastActive.localSettings);
	});
	document.getElementById('livestreamEvents').addEventListener('click', async (e) => {
		if (e.srcElement.id === 'livestreamEvents') {
			helpers.unfocusEvent(lastActive);
		}
	});
}

/**
 * Handler registering function
 * @param {extercomm} extercomm Extercomm instance to use
 * @param {object} meta Metadata from the upper scope
 * @param {function} focusSelf Focus self with binded context to focus the pane
 */
export async function registerHandlers(extercomm, meta, focusSelf) {
	handlers.forEach(handler => {
		extercomm.addEventListener(handler.event, async (e) => {
			if (meta.initiated !== true && handler.shouldBeInitiatedBefore) {
				await init(extercomm);
				meta.initiated = true;
			}
			if (handler.shouldFocus) {
				focusSelf();
			}
			handler.execute(e, extercomm, lastActive, eventStorage);
		});
	});
}
