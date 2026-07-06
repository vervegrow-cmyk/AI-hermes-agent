export default {
	icon: 'far fa-presentation',
	name: 'showcaseMode',
	label: 'Showcase Mode',
	description: `Toggles the Showcase Mode of the Scenario Editor.
	In this mode, module configurations <strong>are't popping up</strong> when adding a new module.
	This mode is useful when you want to quickly build a scenario and you don't want to setup the actual module.
	To <strong>leave</strong> the Showcase Mode, run this tool again or save the scenario and refresh the browser window.`,
	theme: '#61beed',
	steps: [
		{
			type: 'api',
			method: 'showcaseMode',
			response: {
				output: '{{result}}'
			}
		}
	]
};
