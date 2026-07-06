import * as DManip from '../../../lib/DManip.mjs';
import * as helpers from './helpers.mjs';
/* global IML, Loader, Color, Formula, jsyaml */

import toolTemplate from './inbuilt/toolTemplate.mjs';

/**
 * @description Draws inbuilt tools to tools card
 * @param {object} extercomm Extercomm instance to use
 * @param {array} tools Tools storage
 * @param {object} lastActive Last active object storage
 */
export async function drawTools(extercomm, tools, lastActive) {
	lastActive.editor = false;
	lastActive.tool = null;
	helpers.clearPanes();
	const toolsWrapper = document.getElementById('toolsRow');
	document.getElementById('toolsWrapper').addEventListener('click', (e) => {
		if (e.srcElement.id === 'toolsWrapper' || e.srcElement.id === 'toolsRow') {
			helpers.unfocusTool(lastActive);
		}
	});
	const localTools = await helpers.getLocalTools();
	const localToolsArray = Object.keys(localTools).map(k => localTools[k]);
	(tools.concat(localToolsArray)).forEach((toolBase) => {
		const toolWrapper = DManip.createElement('div', ['col-xl-2', 'col-lg-4', 'col-md-6', 'p-2', 'tool-card-wrapper']);
		if (toolBase.hidden === true) {
			toolWrapper.classList.add('d-none');
			lastActive.hiddenTools.push(toolWrapper);
		}
		const tool = DManip.createElement('div', ['card', 'd-flex', 'tool-card']);
		const toolBody = DManip.createElement('div', ['card-body', 'flex-column', 'text-center', 'pt-2', 'px-0']);
		const toolIcon = DManip.createElement('div', ['p-2', 'tool-icon'], `<i class="fa-fw ${toolBase.icon}"></i>`);
		toolWrapper.appendChild(DManip.createElement('span', ['tool-search-fulltext'], `${toolBase.label}`));
		toolBody.appendChild(toolIcon);
		toolBody.appendChild(DManip.createElement('div', ['tool-label', 'mt-2'], `<p class="lead text-truncate mb-0">${toolBase.label}</p>`));
		if (Object.keys(localTools).includes(toolBase.name)) {
			const codeEdit = DManip.createElement('div', ['tool-edit', 'm-0', 'p-0'], `<span class="font-weight-light stick-with-prev">EDIT CODE</span>`);
			codeEdit.addEventListener('click', () => {
				openToolEditor(extercomm, tools, lastActive, toolBase);
			});
			toolBody.appendChild(codeEdit);
		}
		tool.appendChild(toolBody);
		const color = new Color(toolBase.theme);
		const hoverQ = 20;
		const activeQ = 40;
		tool.addEventListener('click', (e) => {
			if (!e.srcElement.classList.contains('stick-with-prev')) {
				helpers.highlight(tool, color.darker(activeQ).toHex(), lastActive.tool, lastActive.toolColor);
				lastActive.tool = tool;
				lastActive.toolColor = color.toHex();
				drawToolWindow(extercomm, toolBase, lastActive);
			}
		});
		toolWrapper.appendChild(tool);
		tool.style.color = color.determineForegroundColor().toHex();
		tool.style.backgroundColor = color.toHex();
		tool.onmouseover = function f() {
			if (this.classList.contains('active')) {
				return;
			}
			this.style.color = color.darker(hoverQ).determineForegroundColor().toHex();
			this.style.backgroundColor = color.darker(hoverQ).toHex();
		};
		tool.onmouseout = function f() {
			if (this.classList.contains('active')) {
				return;
			}
			this.style.color = color.determineForegroundColor().toHex();
			this.style.backgroundColor = color.toHex();
		};
		toolsWrapper.appendChild(toolWrapper);
	});

	if (await helpers.isAdmin(extercomm)) {
		const toolWrapper = DManip.createElement('div', ['col-xl-2', 'col-lg-3', 'col-md-6', 'p-2', 'tool-card-wrapper']);
		const tool = DManip.createElement('div', ['card', 'd-flex', 'tool-card', 'tool-add']);
		const toolBody = DManip.createElement('div', ['card-body', 'flex-column', 'text-center', 'pt-2', 'px-0']);
		const toolIcon = DManip.createElement('div', ['p-2', 'tool-icon'], `<i class="fa-fw far fa-plus"></i>`);
		toolWrapper.appendChild(DManip.createElement('span', ['tool-search-fulltext'], `Add new snippet`));
		toolBody.appendChild(toolIcon);
		toolBody.appendChild(DManip.createElement('div', ['tool-label', 'mt-2'], `<p class="lead text-truncate mb-0">Add new</p>`));
		tool.appendChild(toolBody);
		tool.addEventListener('click', (e) => {
			if (!e.srcElement.classList.contains('stick-with-prev')) {
				openToolEditor(extercomm, tools, lastActive);
			}
		});
		toolWrapper.appendChild(tool);
		toolsWrapper.appendChild(toolWrapper);
	}
}

/**
 * @description Appends a new tool
 * @param {object} extercomm Extercomm instance to use
 * @param {array} toolBase Config of the new tool
 * @param {object} lastActive Last active object storage
 */
export function pushNewTool(extercomm, toolBase, lastActive) {
	if (lastActive.editor) {
		return;
	}
	const toolsWrapper = document.getElementById('toolsRow');
	const toolWrapper = DManip.createElement('div', ['col-xl-2', 'col-lg-3', 'col-md-6', 'p-2', 'tool-card-wrapper']);
	const tool = DManip.createElement('div', ['card', 'd-flex', 'tool-card']);
	const toolBody = DManip.createElement('div', ['card-body', 'flex-column', 'text-center', 'pt-2', 'px-0']);
	const toolIcon = DManip.createElement('div', ['p-2', 'tool-icon'], `<i class="fa-fw ${toolBase.icon}"></i>`);
	toolWrapper.appendChild(DManip.createElement('span', ['tool-search-fulltext'], `${toolBase.label}`));
	toolBody.appendChild(toolIcon);
	toolBody.appendChild(DManip.createElement('div', ['tool-label', 'mt-2'], `<p class="lead">${toolBase.label}</p>`));
	tool.appendChild(toolBody);
	tool.addEventListener('click', () => {
		helpers.highlight(tool, toolBase.theme.active, lastActive.tool, lastActive.toolColor);
		lastActive.tool = tool;
		lastActive.toolColor = toolBase.theme.base;
		drawToolWindow(extercomm, toolBase, lastActive);
	});
	toolWrapper.appendChild(tool);
	tool.style.color = (new Color(toolBase.theme.base)).determineForegroundColor().toHex();
	tool.style.backgroundColor = toolBase.theme.base;
	tool.onmouseover = function f() {
		if (this.classList.contains('active')) {
			return;
		}
		this.style.color = (new Color(toolBase.theme.hover)).determineForegroundColor().toHex();
		this.style.backgroundColor = toolBase.theme.hover;
	};
	tool.onmouseout = function f() {
		if (this.classList.contains('active')) {
			return;
		}
		this.style.color = (new Color(toolBase.theme.base)).determineForegroundColor().toHex();
		this.style.backgroundColor = toolBase.theme.base;
	};
	toolsWrapper.appendChild(toolWrapper);
}

/**
 * @description Draws a right pane content for the picked tool
 * @param {object} extercomm Extercomm instance to use
 * @param {object} toolBase Config of the tool
 * @param {object} lastActive Last active object storage
 */
export function drawToolWindow(extercomm, toolBase, lastActive) {
	Forman.registerLoaderProtocolHandler('rpc', async (source, options) => {
		if (toolBase.rpcs) {
			const rpcToExecute = toolBase.rpcs.find(r => source.includes(r.name));
			if (!rpcToExecute) {
				throw new Error('RPC doesn\'t exist.');
			} else {
				return (await evaluateSteps(extercomm, rpcToExecute.steps, options));
			}
		} else {
			throw new Error('RPC doesn\'t exist.');
		}
	});

	const toolWindow = document.getElementById('toolWindow');
	toolWindow.innerHTML = '';
	toolWindow.appendChild(makeToolStep(extercomm, toolBase, lastActive));
}

/**
 * @description Opens a tool editor to edit the code of the tool
 * @param {object} extercomm Extercomm instance to use
 * @param {array} tools Available tools array
 * @param {object} lastActive Last active object pointer
 * @param {object} toolBase Tool base to be opened
 */
export function openToolEditor(extercomm, tools, lastActive, toolBase) {
	lastActive.editor = true;
	helpers.unfocusTool(lastActive);
	let isNew = false;
	if (!toolBase) {
		toolBase = toolTemplate;
		isNew = true;
	}
	const toolsWrapper = document.getElementById('toolsRow');
	toolsWrapper.innerHTML = '';
	const editorWrapper = DManip.makeToolEditor(toolBase);
	toolsWrapper.appendChild(editorWrapper);
	const buttonBar = DManip.createElement('dd', ['d-flex', 'flex-row-reverse', 'col-12', 'm-0', 'p-3']);
	if (isNew) {
		const cancelButton = DManip.createElement('button', ['btn', 'btn-secondary', 'ml-3'], 'Cancel');
		cancelButton.setAttribute('type', 'button');
		const successButton = DManip.createElement('button', ['btn', 'btn-primary', 'ml-3'], 'Add');
		const errorBar = DManip.createElement('p', ['text-danger', 'my-auto']);
		successButton.setAttribute('type', 'button');
		cancelButton.addEventListener('click', () => {
			drawTools(extercomm, tools, lastActive);
		});
		successButton.addEventListener('click', async () => {
			const localTools = await helpers.getLocalTools();
			try {
				const editedTool = jsyaml.safeLoad(window.currentToolEdit.getValue());
				if (localTools[editedTool.name]) {
					errorBar.innerHTML = 'This tool name is already taken. Please choose a different one.';
					return;
				}
				localTools[editedTool.name] = editedTool;
				await helpers.saveLocalTools(localTools);
				drawTools(extercomm, tools, lastActive);
			} catch (err) {
				errorBar.innerHTML = 'Tool code isn\'t a valid YAML structure.';
			}
		});
		buttonBar.appendChild(cancelButton);
		buttonBar.appendChild(successButton);
		buttonBar.appendChild(errorBar);
	} else {
		const deleteButton = DManip.createElement('button', ['btn', 'btn-danger', 'ml-3'], 'Delete');
		deleteButton.setAttribute('type', 'button');
		const cancelButton = DManip.createElement('button', ['btn', 'btn-secondary', 'ml-3'], 'Leave');
		cancelButton.setAttribute('type', 'button');
		const successButton = DManip.createElement('button', ['btn', 'btn-primary', 'ml-3'], 'Save');
		const errorBar = DManip.createElement('p', ['text-danger', 'my-auto']);
		successButton.setAttribute('type', 'button');
		deleteButton.addEventListener('click', async () => {
			const localTools = await helpers.getLocalTools();
			delete localTools[toolBase.name];
			await helpers.saveLocalTools(localTools);
			drawTools(extercomm, tools, lastActive);
		});
		cancelButton.addEventListener('click', () => {
			drawTools(extercomm, tools, lastActive);
		});
		successButton.addEventListener('click', async () => {
			const localTools = await helpers.getLocalTools();
			try {
				const editedTool = jsyaml.safeLoad(window.currentToolEdit.getValue());
				if (editedTool.name != toolBase.name && localTools[editedTool.name]) {
					errorBar.innerHTML = 'This tool name is already taken. Please choose a different one.';
					return;
				}
				if (editedTool.name != toolBase.name) {
					delete localTools[toolBase.name];
				}
				localTools[editedTool.name] = editedTool;
				await helpers.saveLocalTools(localTools);
				drawTools(extercomm, tools, lastActive);
			} catch (err) {
				errorBar.innerHTML = 'Tool code isn\'t a valid YAML structure.';
			}
		});
		buttonBar.appendChild(deleteButton);
		buttonBar.appendChild(cancelButton);
		buttonBar.appendChild(successButton);
		buttonBar.appendChild(errorBar);
	}
	editorWrapper.appendChild(buttonBar);
	window.mirrorify();
}

/**
 * @description Evaluates steps
 * @param {object} extercomm Extercomm instance to use
 * @param {array} steps Steps to evaluate
 * @param {object} options Options and parameters
 * @return {object} Return value of the tool
 */
async function evaluateSteps(extercomm, steps, options) {
	const temp = {};
	let toReturn = {};
	for (const step of steps) {
		const result = await evaluateStep(extercomm, step, options.data);
		if (step.response) {
			const output = processResponse(step.response, result, temp, options.data);
			if (step.response.output) {
				toReturn = output;
			}
		}
	}
	return toReturn;
}

/**
 * @description Evaluates the step
 * @param {object} extercomm Extercomm instance to use
 * @param {object} step Step to evaluate
 * @param {object} parameters Patameters
 * @return {object} Response
 */
async function evaluateStep(extercomm, step, parameters) {
	switch (step.type) {
		case 'javascript':
			const code = Array.isArray(step.code) ? step.code.join(' ') : step.code;
			return await extercomm.evaluate(`((parameters) => {${code}})(${JSON.stringify(parameters)})`);
		case 'api':
			return await extercomm.send(step.method, parameters);
		case 'local':
			return await step.executor(parameters);
		case 'loader':
			return await new Promise(async (resolve, reject) => {
				Loader.load(step.request.url, {}, (err, data) => {
					if (err) {
						reject(err);
					} else {
						resolve(data);
					}
				});
			});
	}
}

/**
 * @description Processes the response
 * @param {object} response Response to process
 * @param {object} result Result to process
 * @param {object} temp Temp storage
 * @param {object} parameters Parameters
 * @return {object} Output
 */
export function processResponse(response, result, temp, parameters) {
	if (response.temp) {
		Object.keys(response.temp).forEach(key => {
			temp[key] = IML.execute(IML.parse(response.temp[key]), { result: result, parameters: parameters });
		});
	}
	if (response.iterate) {
		let toIterate = [];
		if (typeof response.iterate === 'object') {
			toIterate = IML.execute(IML.parse(response.iterate.container), { result: result, temp: temp, parameters: parameters });
			if (response.iterate.condition) {
				toIterate = toIterate.filter(item => IML.execute(IML.parse(response.iterate.condition), { item: item, temp: temp, parameters: parameters }));
			}
		} else {
			toIterate = IML.execute(IML.parse(response.iterate), { result: result, temp: temp, parameters: parameters });
		}
		if (response.output) {
			const output = toIterate.map(item => {
				const element = {};
				Object.keys(response.output).forEach(key => {
					element[key] = IML.execute(IML.parse(response.output[key]), { item: item, parameters: parameters });
				});
				return element;
			});
			return output;
		}
	} else if (response.output) {
		if (typeof response.output === 'object') {
			const output = {};
			Object.keys(response.output).forEach(key => {
				output[key] = IML.execute(IML.parse(response.output[key]), { result: result, parameters: parameters });
			});
			return output;
		} else {
			return IML.execute(IML.parse(response.output), { result: result, parameters: parameters });
		}
	}
}

/**
 * @description Generates a new tool step card
 * @param {object} extercomm Extercomm instance to use
 * @param {object} toolBase Input
 * @param {object} lastActive Last active object storage
 * @return {object} New card
 */
export function makeToolStep(extercomm, toolBase, lastActive) {
	const card = DManip.createElement('div', ['card']);
	const cardBody = DManip.createElement('div', ['card-body']);
	const cardHeader = DManip.createElement('div', [], `<h5>${toolBase.label}</h5><p class="font-weight-light">${toolBase.description}</p>`);
	if (toolBase.modifier === true) {
		cardHeader.innerHTML += `
		<p class="text-danger font-weight-bold">
			<i class="far fa-exclamation-triangle"></i> This tool will modify the scenario. Make sure you know what you're doing.
		</p>
		`;
	}
	cardBody.appendChild(cardHeader);
	const button = DManip.createElement('button', ['btn', 'btn-primary'], 'Run');
	button.setAttribute('type', 'button');
	if (toolBase.input && toolBase.input.length !== 0) {
		const form = document.createElement('imt-forman');
		form.build(toolBase.input).then(() => {
			button.addEventListener('click', async () => {
				button.setAttribute('disabled', true);
				button.innerHTML = `Working...`;
				if (form.validate()) {
					const response = await evaluateSteps(extercomm, toolBase.steps, { data: form.value });
					if (toolBase.modifier === true) {
						await extercomm.send('revalidateAndRerender', {});
					}
					card.parentElement.insertBefore(DManip.makeToolResponse(response, helpers.unfocusTool, lastActive), card.nextElementSibling);
					card.classList.add('d-none');
					window.mirrorify();
				}
			});
			form.appendChild(button);
		});
		cardBody.appendChild(form);
	} else {
		const noform = DManip.createElement('div', [], `
		<div class="text-center">
			<p class="lead">No parameters required.</p>
		</div>`);
		button.addEventListener('click', async () => {
			button.setAttribute('disabled', true);
			button.innerHTML = `Working...`;
			const response = await evaluateSteps(extercomm, toolBase.steps, { data: {} });
			if (toolBase.modifier === true) {
				await extercomm.send('rerender', {});
			}
			card.parentElement.insertBefore(DManip.makeToolResponse(response, helpers.unfocusTool, lastActive), card.nextElementSibling);
			card.classList.add('d-none');
			window.mirrorify();
		});
		noform.appendChild(button);
		cardBody.appendChild(noform);
	}
	card.appendChild(cardBody);
	return card;
}
