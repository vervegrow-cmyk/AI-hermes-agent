export default {
	icon: 'fad fa-exchange-alt',
	name: 'base64',
	label: 'Base 64',
	description: 'Use this tool to simply encode and decode Base64 strings.',
	theme: '#EEEEEE',
	input: [
		{
			name: 'operation',
			label: 'Operation',
			type: 'select',
			mappable: false,
			editable: false,
			default: 'decode',
			options: [
				{
					value: 'encode',
					label: 'Encode'
				},
				{
					value: 'decode',
					label: 'Decode'
				}
			],
			required: true,
			help: 'Select which operation should be performed.'
		},
		{
			name: 'raw',
			label: 'Raw Data',
			type: 'text',
			multiline: true,
			required: true,
			help: 'Data to be encoded/decoded.'
		}
	],
	steps: [
		{
			type: 'local',
			executor: (parameters) => {
				if (parameters.operation === 'encode') {
					return btoa(parameters.raw);
				} else if (parameters.operation === 'decode') {
					return atob(parameters.raw);
				} else {
					return 'Invalid input.'
				}
			},
			response: {
				output: '{{result}}'
			}
		}
	]
};
