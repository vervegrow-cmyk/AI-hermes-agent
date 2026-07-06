export default {
	icon: 'fas fa-search',
	name: 'focusModule',
	label: 'Focus a Module',
	description: 'Focuses a module by its id.',
	theme: '#EEEEEE',
	input: [
		{
			name: 'module',
			label: 'Module ID',
			type: 'uinteger',
			help: 'Id of the module to focus.',
			required: true
		}
	],
	steps: [
		{
			type: 'api',
			method: 'focusModule'
		}
	]
};
