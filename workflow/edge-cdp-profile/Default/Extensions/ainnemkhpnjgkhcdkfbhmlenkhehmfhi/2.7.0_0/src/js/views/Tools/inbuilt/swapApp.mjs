export default {
	icon: 'far fa-random',
	name: 'swapApp',
	label: 'Swap App',
	description: 'Swaps the given app for another one.',
	theme: '#EEEEEE',
	modifier: true,
	input: [
		{
			name: 'toFind',
			label: 'App to be Replaced',
			type: 'select',
			help: 'Name of the app to be replaced.',
			required: true,
			options: {
				store: 'rpc://listAppsInScenario',
				nested: [
					{
						name: 'srcVersion',
						label: 'Version',
						type: 'select',
						options: 'rpc://listAppVersionsInScenario',
						help: 'Version of the app to be replaced.',
						required: true,
						forceReload: true
					}
				]
			}
		},
		{
			name: 'replaceWith',
			label: 'Replace with',
			help: 'Name of the new app.',
			type: 'select',
			mappable: true,
			required: true,
			options: {
				store: 'rpc://listApps',
				nested: [
					{
						name: 'drainVersion',
						label: 'Version',
						type: 'select',
						help: 'Version of the new app.',
						required: true,
						options: 'rpc://listAppVersions',
						forceReload: true
					}
				]
			}
		}
	],
	steps: [
		{
			type: 'api',
			method: 'swapApp'
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
		},
		{
			name: 'listApps',
			steps: [
				{
					type: 'javascript',
					code: `
						let res = []; Loader.load('/api/apps/list', {async: false}, (e,f) => {res = f});
						const visited = [];
						const out = [];
						res.response.forEach(r => {
							if(!visited.includes(r.name)) {
								visited.push(r.name);
								out.push({label: \`APPS # \${r.label}\`, name: r.name})
							}
						});
						return out;
						`,
					response: {
						temp: {
							apps: '{{result}}'
						}
					}
				},
				{
					type: 'api',
					method: 'loadApps',
					response: {
						iterate: '{{merge(distinct(result.apps, \'name\'), temp.apps)}}',
						output: {
							label: '{{item.label}}',
							value: '{{item.name}}'
						}
					}
				}
			]
		},
		{
			name: 'listAppVersions',
			steps: [
				{
					type: 'javascript',
					code: `
						let res = []; Loader.load('/api/apps/list', {async: false}, (e,f) => {res = f});
						res.response = res.response.filter(r => {return r.name === parameters.replaceWith});
						return res.response.map(r => { return {version: r.version, name: r.name}});
						`,
					response: {
						temp: {
							apps: '{{result}}'
						}
					}
				},
				{
					type: 'api',
					method: 'loadApps',
					response: {
						iterate: {
							container: '{{merge(result.apps, temp.apps)}}',
							condition: '{{item.name === parameters.replaceWith}}'
						},
						output: {
							label: '{{item.version}}',
							value: '{{item.version}}'
						}
					}
				}
			]
		},
	]
};
