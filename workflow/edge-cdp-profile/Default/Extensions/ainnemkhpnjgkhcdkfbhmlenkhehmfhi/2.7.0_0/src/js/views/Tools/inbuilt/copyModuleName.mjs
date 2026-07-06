export default {
	icon: 'far fa-clone',
	name: 'copyModuleName',
	label: 'Copy Module Name',
	description: `
		Copies the name of the selected module to the clipboard.
	`,
	theme: '#EEEEEE',
	input: [
		{
			name: 'source',
			label: 'Module',
			type: 'select',
			options: 'rpc://listModules',
			help: 'Enter the module to copy the name of.',
			mappable: true,
			required: true
		}
	],
	steps: [
		{
			type: 'api',
			method: 'copyModuleName'
		}
	],
	rpcs: [
		{
			name: 'listModules',
			steps: [
				{
					type: 'javascript',
					code: `
						return (Inspector.instance.findObject?.('module') ?? Inspector.instance._surface.find(Surface.Module)).map(m => {return{label:\`\${m.config.label} (\${m.__id})\`,value: m.__id}})
					`,
					response: {
						output: '{{result}}'
					}
				}
			]
		}
	]
};
