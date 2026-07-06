export default {
	icon: 'far fa-presentation',
	name: 'showcaseNames',
	label: 'Mock Labels',
	description: `This tool is able to change the label and description of the given Module.
	It's <strong>not meant</strong> for actual renaming the Modules, for that, use the Scenario Editor directly.
	Changes made by this tool <strong>aren't permanent</strong>, they don't affect the real scenarios
	and are meant only purely for the scenario presentation purposes.
	To <strong>reset</strong> the texts, just refresh the browser window.`,
	theme: '#61beed',
	input: [
		{
			name: 'mdl',
			label: 'Module',
			type: 'select',
			options: {
				store: 'rpc://listModules',
				nested: [
					{
						name: 'label',
						label: 'Label',
						type: 'text',
						help: 'Label of the module. The bold text under the Module. Empty value means no change, if you want to **blank** the field, enter ` ` (space).'
					},
					{
						name: 'description',
						label: 'Description',
						type: 'text',
						help: 'Description of the module. The small text under the Label. Empty value means no change, if you want to **blank** the field, enter ` ` (space).'
					}
				]
			},
			help: 'Select the Module to change the Label and Description.',
			mappable: true,
			required: true
		}
	],
	steps: [
		{
			type: 'api',
			method: 'showcaseNames'
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
