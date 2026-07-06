import * as actions from './actions.mjs';

export default [
	{
		event: 'injectExternalTool',
		shouldFocus: false,
		shouldBeInitiatedBefore: true,
		execute: async (e, extercomm, lastActive, tools) => {
			await extercomm.respond(e.detail.correlationId, {
				success: await injectExternalTool(extercomm, tools, lastActive, e.detail.content)
			});
		}
	}
];

/**
 * @description Pushes a new tool to the tool-list
 * @param {object} extercomm Extercomm instance to use
 * @param {array} tools Tools storage object
 * @param {object} lastActive Last active object storage
 * @param {object} toolBase A new tool description
 * @return {boolean} If the push was successful or not
 */
async function injectExternalTool(extercomm, tools, lastActive, toolBase) {
	if (!!tools.find(tool => tool.name == toolBase.name)) {
		return false;
	}
	tools.push(toolBase);
	actions.pushNewTool(extercomm, toolBase, lastActive);
	return true;
}
