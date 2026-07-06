export default {
	icon: 'far fa-filter',
	name: 'copyFilter',
	label: 'Copy Filter',
	description: `
		Copies a filter.
		The filter is always assigned to the module that's on it's <b>right</b>.
		For example, when you need to copy a filter that's between modules 1 and 2 and place it between modules 3 and 4, 
		then pick the module 2 as the source and the module 4 as the target.`,
	theme: '#EEEEEE',
	modifier: true,
	input: [
		{
			name: 'source',
			label: 'Source Module',
			type: 'select',
			options: 'rpc://listModules',
			help: 'This will copy the filter that\'s on the LEFT side of the selected module.',
			required: true
		},
		{
			name: 'target',
			label: 'Target Module',
			type: 'select',
			options: 'rpc://listModules',
			help: 'This will paste the filter to the LEFT side of the selected module.',
			required: true
		},
		{
			name: 'preserveFallback',
			label: 'Preserve Fallback Route setting',
			type: 'boolean',
			required: true,
			default: false,
			help: 'When checked, then if the filter is used as a fallback route on a router and is copied to another router, then the fallback setting will be preserved, but only if there\'s no another fallback route on the target router.'
		}
	],
	steps: [
		{
			type: 'api',
			method: 'copyFilter'
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
