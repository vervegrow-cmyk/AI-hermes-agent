export default {
	icon: 'far fa-random',
	name: 'remapSource',
	label: 'Remap Source',
	description: `
	Use this tool to remap modules in scenario from one source to another. Optionally, you can specify only one module to be remapped.
	`,
	theme: '#EEEEEE',
	modifier: true,
	input: [
		{
			name: 'source',
			label: 'Source Module',
			type: 'select',
			options: 'rpc://listModules',
			help: 'The original module to be remapped.',
			mappable: true,
			required: true
		},
		{
			name: 'target',
			label: 'Target Module',
			type: 'select',
			options: 'rpc://listModules',
			help: 'The new module to be used as a source for the other modules.',
			mappable: true,
			required: true
		},
		{
			name: 'concrete',
			label: 'Module to Edit',
			type: 'select',
			options: 'rpc://listModules',
			help: 'You can specify only one module to be remapped.',
			mappable: true,
			required: false
		}
	],
	steps: [
		{
			type: 'api',
			method: 'remapSource'
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
