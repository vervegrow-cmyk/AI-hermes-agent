export default {
	icon: 'fas fa-search',
	name: 'searchByConfig',
	label: 'Find module(s) by mapping',
	description: 'Returns IDs of modules with a specified keyword in their mapping.',
	theme: '#EEEEEE',
	input: [
		{
			name: 'keyword',
			label: 'Keyword',
			type: 'text',
			help: 'A keyword to search for.',
			required: true
		},
		{
			name: 'useOnlyValues',
			label: 'Use Only Values',
			type: 'boolean',
			required: true,
			default: true,
			help: 'When using this option, the tool will search only through values. If unchecked, even the keys are considered.'
		}
	],
	steps: [
		{
			type: 'api',
			method: 'searchByConfig',
			response: {
				output: '{{result}}'
			}
		}
	]
};
