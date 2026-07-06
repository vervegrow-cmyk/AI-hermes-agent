export default {
	icon: 'far fa-magic',
	name: 'new-tool',
	label: 'New Tool',
	description: 'This is a new tool.',
	theme: '#EEEEEE',
	input: [
		{
			name: 'module',
			label: 'Module ID',
			type: 'uinteger',
			help: 'Id of the module to perform an action on.'
		}
	],
	steps: [
		{
			type: 'javascript',
			code: 'console.log(parameters.module);'
		}
	]
};
