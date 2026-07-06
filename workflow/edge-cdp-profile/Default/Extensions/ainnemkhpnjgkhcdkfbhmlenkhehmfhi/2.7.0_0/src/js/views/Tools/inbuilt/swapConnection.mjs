export default {
	icon: 'far fa-link',
	name: 'swapConnection',
	label: 'Swap Connection',
	description: `
		The Tool takes the connection from the selected module and sets the same
		connection to all modules of the same app in the scenario.`,
	theme: '#EEEEEE',
	modifier: true,
	input: [
		{
			name: 'sourceModule',
			label: 'Source Module',
			type: 'select',
			options: {
				store: 'rpc://listModules',
				nested: [
					{
						name: 'inModule',
						label: 'Target Module',
						type: 'select',
						options: 'rpc://listModulesOfPackage',
						help: 'Module to swap the connection in. If empty, connection is swapped in the whole scenario.',
						mappable: true,
						forceReload: true
					}
				]
			},
			help: 'Source module to copy the connection from.',
			mappable: true,
			required: true
		},
	],
	steps: [
		{
			type: 'api',
			method: 'swapConnections'
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
		},
		{
			name: 'listModulesOfPackage',
			steps: [
				{
					type: 'api',
					method: 'listModulesOfPackage',
					response: {
						output: '{{result}}'
					}
				}
			]
		}
	]
};
