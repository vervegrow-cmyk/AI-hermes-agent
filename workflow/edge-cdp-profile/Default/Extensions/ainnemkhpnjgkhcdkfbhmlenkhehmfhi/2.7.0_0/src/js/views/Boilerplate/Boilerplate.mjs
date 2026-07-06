import { default as template } from './template.mjs';
export const config = {
	id: 'boilerplate',
	name: 'Boilerplate',
	sidebarIcon: ['far', 'fa-fw', 'fa-box-open'],
	template: template
};

export async function init(extercomm) {
	console.log('The Boilerplate View got initiated right now.');
}

export async function registerHandlers(extercomm, meta, focusSelf) {
	console.log('Registering hanlders for the Boilerplate view.');
	// Using a separate file for the handlers is recommended.
	// Inspire yourself in ScenarioDebugger extension
	extercomm.addEventListener('test', async (e) => {
		await extercomm.respond(e.detail.correlationId, {
			message: 'Hey there!'
		});
	});
}
