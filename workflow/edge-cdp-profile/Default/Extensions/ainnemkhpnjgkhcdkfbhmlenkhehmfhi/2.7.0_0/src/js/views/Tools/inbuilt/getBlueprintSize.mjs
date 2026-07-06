const code = () => {
	try {
		const blueprint = Inspector.instance.scenario.toJSON();
		if (!blueprint) return [ 'Blueprint not collected correctly.' ];
		const flows = [blueprint.flow || [], ...((blueprint.metadata && blueprint.metadata.designer && blueprint.metadata.designer.orphans) ? blueprint.metadata.designer.orphans : [])];

		const sizes = {
			'Blueprint': JSON.stringify(blueprint).length
		};

		let inModules = 0;
		const iterate = (flow) => {
			for (const m of flow) {
				let nestedFlows = [];
				if (m.routes) {
					nestedFlows = m.routes.map(r => r.flow);
					delete m.routes;
				}
				if (m.onerror) {
					nestedFlows.push(m.onerror);
					delete m.onerror;
				}

				const config = JSON.stringify(m);
				sizes[m.id] = config.length;
				inModules += config.length;

				for (const nestedFlow of nestedFlows) iterate(nestedFlow);
			}
		}
		for (const flow of flows) iterate(flow);
		sizes['Structure'] = sizes['Blueprint'] - inModules;

		return Object.entries(sizes)
			.map(([id, size]) => ({
				id, size
			}))
			.sort((a, b) => a.size > b.size ? -1 : a.size < b.size ? 1 : 0)
			.map(block => `${Number.isNaN(parseInt(block.id)) ? '' : 'Module '}${block.id} has ${block.size} bytes.`);
	} catch(err) {
		console.error(err);
		return [ 'Something went wrong while counting the Blueprint size.' ];
	}
};

export default {
	icon: 'far fa-sort-size-down',
	name: 'getBlueprintSize',
	label: 'Get Blueprint Size',
	description: 'Use this tool to check the size of particular Modules in the Scenario. Useful when having troubles saving too large Blueprint.',
	theme: '#D7A8E4',
	input: [
	],
	steps: [
		{
			type: 'javascript',
			code: `return (${code.toString()})()`,
			response: {
				output: '{{result}}'
			}
		}
	]
};
