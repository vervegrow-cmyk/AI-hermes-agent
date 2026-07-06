export default {
	icon: 'far fa-clone',
	name: 'copyMapping',
	label: 'Copy Mapping',
	description: 'Copies mapping from one module to another.',
	theme: '#EEEEEE',
	modifier: true,
	input: [
		{
			name: 'source',
			label: 'Source Module',
			type: 'select',
			options: 'rpc://listModules',
			help: 'Source module to get the mapping.',
			mappable: true,
			required: true
		},
		{
			name: 'target',
			label: 'Target Module',
			type: 'select',
			options: 'rpc://listModules',
			help: 'Target module to paste the mapping.',
			mappable: true,
			required: true
		}
	],
	steps: [
		{
			type: 'api',
			method: 'copyMapping'
		}
	],
	rpcs: [
		{
			name: 'listModules',
			steps: [
				{
					type: 'api',
					method: 'listAvailableModules',
					response: {
						output: '{{result}}'
					}
				}
			]
		}
	]
};
