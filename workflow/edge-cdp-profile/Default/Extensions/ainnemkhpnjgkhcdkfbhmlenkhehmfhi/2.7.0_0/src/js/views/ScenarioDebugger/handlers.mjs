import * as helpers from './helpers.mjs';
import * as actions from './actions.mjs';

export default [
	{
		event: 'focusModuleCycleOperation',
		shouldFocus: true,
		shouldBeInitiatedBefore: true,
		execute: async (e, extercomm, lastActive) => {
			const c = e.detail.content;
			await extercomm.respond(e.detail.correlationId, {
				success: await focusModuleCycleOperation(extercomm, lastActive, c.module, c.cycle, c.operation)
			});
		}
	}
];

/**
* @description Focuses the specified module-cycle-operation in the view
* @param {Extercomm} extercomm An instance of the Extercomm to use
* @param {object} lastActive Last active instances
* @param {Number} moduleId ID of the module
* @param {Number} cycleIndex n-th cycle index
* @param {Number} operationIndex m-th operation index
* @return {Boolean} Returns true when the focus succeeded, otherwise false
*/
async function focusModuleCycleOperation(extercomm, lastActive, moduleId, cycleIndex, operationIndex) {
	const module = document.getElementById(`module-${moduleId}`);
	if (!module) {
		return false;
	}
	lastActive.module = helpers.highlight(module, lastActive.module);
	helpers.scrollIntoView(lastActive.module);
	await actions.listModuleCycles(extercomm, lastActive, moduleId);
	if (!cycleIndex) {
		return true;
	}
	if (!operationIndex) {
		return true;
	}
	const operation = document.getElementById(`cycle${cycleIndex}operation${operationIndex}`);
	if (!operation) {
		return false;
	}
	lastActive.operation = helpers.highlight(operation, lastActive.operation);
	helpers.scrollIntoView(lastActive.operation);
	await actions.listModuleOperationEvents(extercomm, moduleId, cycleIndex, operationIndex);
	return true;
}
