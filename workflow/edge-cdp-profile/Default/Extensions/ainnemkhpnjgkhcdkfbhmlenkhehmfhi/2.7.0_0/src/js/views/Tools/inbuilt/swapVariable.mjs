export default {
	icon: 'far fa-random',
	name: 'swapVariable',
	label: 'Swap Variable',
	description: `
		Finds all occurrences of the given variable across whole scenario or in one module and
		replaces them with the new one. Wildcards are not supported. For example,
		let's have an object "{ a: { b: 1, c: 2 } }". You can swap \`a.b\` for \`a.c\`,
		but you can't swap \`a\` for \`d\``,
	theme: '#EEEEEE',
	modifier: true,
	input: [
		{
			name: 'toFind',
			label: 'Variable to find',
			type: 'text',
			help: 'Simply copy and paste the variable pill the from scenario. The value should look like "{{12.Items}}" or "{{13.Items[].Code}}"',
			required: true
		},
		{
			name: 'replaceWith',
			label: 'Replace with',
			type: 'text',
			help: 'Simply copy and paste the variable pill the from scenario. The value should look like "{{12.Items}}" or "{{13.Items[].Code}}"',
			required: true
		},
		{
			name: 'inModule',
			label: 'Module',
			type: 'select',
			options: 'rpc://listModules',
			help: 'Module to swap the variable in. If empty, variable is swapped in whole scenario.',
			mappable: true
		},
	],
	steps: [
		{
			type: 'api',
			method: 'swapVariable'
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
