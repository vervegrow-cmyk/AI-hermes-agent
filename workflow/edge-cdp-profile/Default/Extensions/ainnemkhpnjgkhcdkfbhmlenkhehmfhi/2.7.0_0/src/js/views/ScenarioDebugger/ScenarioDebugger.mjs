import * as helpers from './helpers.mjs';
import * as actions from './actions.mjs';
import handlers from './handlers.mjs';
import * as ChromeAsync from '../../../lib/ChromeAsync.mjs';

import { default as template } from './template.mjs';
export const config = {
	id: 'scenarioDebugger',
	name: 'Scenario Debugger',
	sidebarIcon: ['far', 'fa-fw', 'fa-share-alt'],
	template: template
};

const lastActive = { module: null, operation: null };

/**
 * Main initializer function
 * @param {extercomm} extercomm Extercomm instance to use
 */
export async function init(extercomm) {
	document.getElementById('moduleSearch').addEventListener('keyup', helpers.moduleSearch);
	document.getElementById('scenarioDebuggerOpenHelp').addEventListener('click', async () => {
		await ChromeAsync.openTab(`https://www.make.com/en/help/scenarios/make-devtool#scenario-debugger`);
	});
	document.getElementById('moduleListItems').addEventListener('click', async (e) => {
		if (e.srcElement.id === 'moduleListItems') {
			helpers.unfocusModule(lastActive);
		}
	});
	document.getElementById('cycleListItems').addEventListener('click', async (e) => {
		if (e.srcElement.id === 'cycleListItems') {
			helpers.unfocusOperation(lastActive);
		}
	});
	await actions.listModules(extercomm, lastActive);
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
			handler.execute(e, extercomm, lastActive);
		});
	});
}
