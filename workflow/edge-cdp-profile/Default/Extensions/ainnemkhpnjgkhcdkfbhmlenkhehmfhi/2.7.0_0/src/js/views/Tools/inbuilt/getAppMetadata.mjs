export default {
	icon: 'fas fa-search',
	name: 'getAppId',
	label: 'Get App Metadata',
	description: 'Retrieves metadata of the selected app.',
	theme: '#EEEEEE',
	input: [
		{
			name: 'sourceModule',
			label: 'Source Module',
			type: 'select',
			options: 'rpc://listModules',
			help: 'Source module to get the metadata of.',
			mappable: true,
			required: true
		}
	],
	steps: [
		{
			type: 'api',
			method: 'getAppMetadata',
			response: {
				output: '{{result}}'
			}
		}
	],
	rpcs: [
		{
			name: 'listModules',
			steps: [
				{
					type: 'api',
					method: 'getAppMetadataListModules',
					response: {
						output: '{{result}}'
					}
				}
			]
		}
	]
};
