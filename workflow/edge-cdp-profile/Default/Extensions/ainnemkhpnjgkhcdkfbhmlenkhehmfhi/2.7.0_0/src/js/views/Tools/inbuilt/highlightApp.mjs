export default {
	icon: 'far fa-highlighter',
	name: 'highlightApp',
	label: 'Highlight App',
	description: 'Use this tool to highlight a specific version of the App in your scenario',
	theme: '#EEEEEE',
	input: [
		{
			name: 'toFind',
			label: 'App to be highlighted',
			type: 'select',
			help: 'Name of the app to be highlighted.',
			required: true,
			options: {
				store: 'rpc://listAppsInScenario',
				nested: [
					{
						name: 'srcVersion',
						label: 'Version',
						type: 'select',
						options: 'rpc://listAppVersionsInScenario',
						help: 'Version of the app to be highlighted.',
						required: true,
						forceReload: true
					}
				]
			}
		},
		{
			name: 'color',
			type: 'color',
			label: 'Highlight Color',
			help: 'Color to use when highlighting.',
			required: true,
			default: '#FF00FF'
		}
	],
	steps: [
		{
			type: 'api',
			method: 'highlightApp'
		}
	],
	rpcs: [
		{
			name: 'listAppsInScenario',
			steps: [
				{
					type: 'api',
					method: 'listAppsInScenario',
					response: {
						output: '{{result}}'
					}
				}
			]
		},
		{
			name: 'listAppVersionsInScenario',
			steps: [
				{
					type: 'api',
					method: 'listAppVersionsInScenario',
					response: {
						output: '{{result}}'
					}
				}
			]
		}
	]
};
