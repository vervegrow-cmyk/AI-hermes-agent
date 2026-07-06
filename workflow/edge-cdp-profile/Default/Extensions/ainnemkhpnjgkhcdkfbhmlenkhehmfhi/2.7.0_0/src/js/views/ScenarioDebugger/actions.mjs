import * as DManip from '../../../lib/DManip.mjs';
import * as Exporter from '../../../lib/Exporter.mjs';

import * as common from '../../../lib/common.mjs';
import * as helpers from './helpers.mjs';

/**
 * @description Retrieves a list of modules in the scenario
 * @param {Extercomm} extercomm An instance of the Extercomm to use3
 * @param {object} lastActive Last active instances
 */
export async function listModules(extercomm, lastActive) {
	const response = await extercomm.send('listModules', {});
	// If no modules are available
	if (Array.isArray(response) && response.length === 0) {
		document.getElementById('moduleListItems').innerHTML = `
		<li class="my-auto text-center font-weight-bold text-secondary lead">
			Nothing to show. ¯\\_(ツ)_/¯
		</li>`;
		helpers.unfocusModule(lastActive);
		return;
	}
	const moduleListItems = document.getElementById('moduleListItems');
	moduleListItems.innerHTML = '';
	response.forEach(module => {
		const item = DManip.createElement('li', ['list-group-item', 'd-flex', 'align-items-center', 'py-0']);

		// Module theme and icon
		const imageWrapper = DManip.createElement('div', ['py-2', 'px-0']);
		const theme = DManip.createElement('div', ['module-theme']);

		const matchResults =  /([a-z][0-9a-z-]+[0-9a-z]\.png)/.exec(module.icon);
		if (matchResults.length > 1) {
			const img = DManip.createElement('img', ['module-icon-img']);
			const icon = DManip.createElement('div', ['module-icon']);
			img.setAttribute('src', module.iconB64);
			img.setAttribute('width', 36);
			img.setAttribute('height', 36);
			icon.appendChild(img);
			theme.appendChild(icon);
		}

		theme.setAttribute('style', `background-color: ${module.theme}`);
		imageWrapper.appendChild(theme);
		item.appendChild(imageWrapper);

		// Module name
		const textWrapper = DManip.createElement('div', ['p-2']);
		textWrapper.appendChild(DManip.createElement('p', ['font-weight-bold', 'mb-0'], `${module.name}`));
		textWrapper.appendChild(DManip.createElement('p', ['mb-0'], `${module.description}`));
		item.appendChild(textWrapper);

		// Module ID
		const idWrapper = DManip.createElement('div', ['ml-auto p-2'], `<div class="module-number text-secondary"><div>${module.id}</div></div>`);
		if (module.id >= 100) {
			idWrapper.classList.add('condensed');
		}
		item.appendChild(idWrapper);

		// Module SEARCH
		item.appendChild(DManip.createElement('span', ['module-search-fulltext'], `${module.name} ${module.description} ${module.id}`));

		item.setAttribute('id', `module-${module.id}`);
		item.addEventListener('click', () => {
			lastActive.module = helpers.highlight(item, lastActive.module);
		});
		item.addEventListener('click', async () => {
			helpers.setPanes([
				{ id: 'event', html: '<li class="my-auto text-center font-weight-bold text-secondary lead">No operation selected</li>' }
			]);
			listModuleCycles(extercomm, lastActive, module.id);
		});
		item.addEventListener('dblclick', async () => {
			const res = await helpers.focusModule(extercomm, module.id);
			if (!res) {
				console.warn('Module focus failed.');
			}
		});
		moduleListItems.appendChild(item);
	});
}

/**
 * @description Retrieves a list of module cycles and operations within those cycles of the module
 * @param {Extercomm} extercomm An instance of the Extercomm to use
 * @param {object} lastActive Last active instances
 * @param {Number} moduleId ID of the module
 */
export async function listModuleCycles(extercomm, lastActive, moduleId) {
	let response;
	try {
		response = await extercomm.send('listModuleCycles', { module: moduleId });
	} catch (err) {
		document.getElementById('cycleListItems').innerHTML = `<li class="my-auto text-center font-weight-bold text-error lead">${err.message}</li>`;
		return;
	}
	if (Array.isArray(response) && response.length === 0) {
		document.getElementById('cycleListItems').innerHTML = `
		<li class="my-auto text-center font-weight-bold text-secondary lead">
			Nothing to show. ¯\\_(ツ)_/¯
		</li>`;
		return;
	}
	const cycleListItems = document.getElementById('cycleListItems');
	cycleListItems.innerHTML = '';
	// For each cycle generate the list of operations
	response.forEach((c, ci) => {
		/**
		 * Both cycle and operation bars in the list are classified as list-group-item
		 * The difference between the cycle and operation is done by
		 * specifying the cycle as "div" and operation as "li"
		 */
		const cycle = DManip.createElement('div', ['list-group-item', 'd-flex', 'align-items-center']);
		cycle.appendChild(DManip.createElement('div', [''], `<span class="font-weight-bold">${c.label}</span>`));
		cycle.addEventListener('click', () => {
			helpers.unfocusOperation(lastActive);
		});
		cycleListItems.appendChild(cycle);

		c.operations.forEach((o, oi) => {
			const order = oi % 2 === 0 ? 'odd' : 'even';
			const operation = DManip.createElement('li', ['list-group-item', 'd-flex', 'align-items-center', `${order}`]);
			operation.setAttribute('id', `cycle${ci + 1}operation${oi + 1}`);

			// Operation icon
			const imageWrapper = DManip.createElement('div', ['py-0', 'pr-2']);
			const operationStatus = DManip.createElement('span', ['operation-status-icon']);
			switch (o.status) {
				case 1:
					operationStatus.innerHTML = `<i class="fas fa-fw fa-check-circle"></i>`;
					operationStatus.classList.add('success');
					break;
				case 2:
					operationStatus.innerHTML = `<i class="fas fa-fw fa-exclamation-triangle"></i>`;
					operationStatus.classList.add('warning');
					break;
				default:
					operationStatus.innerHTML = `<i class="fas fa-fw fa-exclamation-triangle"></i>`;
					operationStatus.classList.add('error');
					break;

			}
			imageWrapper.appendChild(operationStatus);
			operation.appendChild(imageWrapper);

			// Operation name
			const textWrapper = DManip.createElement('div', ['px-0']);
			textWrapper.appendChild(DManip.createElement('p', ['mb-0'], `${o.label}`));
			operation.appendChild(textWrapper);

			// Module ID
			const idWrapper = DManip.createElement('div', ['ml-auto p-0'], `<div class="text-secondary small">${o.duration}ms</div>`);
			operation.appendChild(idWrapper);

			operation.addEventListener('click', () => {
				lastActive.operation = helpers.highlight(operation, lastActive.operation);
			});
			operation.addEventListener('click', async () => {
				listModuleOperationEvents(extercomm, moduleId, ci, oi);
			});
			operation.addEventListener('dblclick', async () => {
				const res = await helpers.focusModule(extercomm, moduleId, ci + 1, oi + 1);
				if (!res) {
					console.warn('Module Cycle Operation focus failed.');
				}
			});

			cycleListItems.appendChild(operation);
		});
	});
}

/**
 * @description Retrieves a list of events inside the operation within the cycle of the module
 * @param {Extercomm} extercomm An instance of the Extercomm to use
 * @param {Number} moduleId ID of the module
 * @param {Number} cycleIndex n-th cycle index
 * @param {Number} operationIndex m-th operation index
 */
export async function listModuleOperationEvents(extercomm, moduleId, cycleIndex, operationIndex) {
	let response;
	try {
		response = await extercomm.send('listModuleOperationEvents', { module: moduleId, cycle: cycleIndex + 1, operation: operationIndex + 1 });
	} catch (err) {
		document.getElementById('eventListItems').innerHTML = `<li class="my-auto text-center font-weight-bold text-error lead">${err.message}</li>`;
		return;
	}
	const eventListItems = document.getElementById('eventListItems');
	eventListItems.innerHTML = '';
	if (!response) {
		return;
	}
	if (Array.isArray(response) && response.length === 0) {
		document.getElementById('eventListItems').innerHTML = `
		<li class="my-auto text-center font-weight-bold text-secondary lead">
			Nothing to show. ¯\\_(ツ)_/¯
		</li>`;
		return;
	}
	const filtered = [];
	let requestsCount = 0;
	let lastRequest = undefined;
	// Filter events and pair requests with responses
	response.forEach((e) => {
		switch (e.type) {
			case 'message':
			case 'profile':
			case 'error':
				filtered.push(e);
				break;
			case 'request':
			case 'query':
				lastRequest = e;
				requestsCount++;
				filtered.push(e);
				break;
			case 'response':
			case 'result':
				if (lastRequest) {
					lastRequest.response = e;
					lastRequest = undefined;
				} else {
					filtered.push(e);
				}
				break;
		}
	});
	if (lastRequest !== undefined) {
		console.warn('Last request doesn\'t have response.');
		lastRequest.response = false;
	}
	// For each of the filtered event generate the event bar
	filtered.forEach((e, ei) => {
		const imtDetail = DManip.createElement('div', ['card']);
		const imtDetailHeader = DManip.createElement('div', ['card-header', 'd-flex', 'py-1', 'pl-2', 'pr-1', 'border-bottom']);
		imtDetailHeader.setAttribute('id', `eventHeader${ei}`);
		imtDetailHeader.setAttribute('data-toggle', 'collapse');
		imtDetailHeader.setAttribute('data-target', `#eventDetail${ei}`);
		imtDetailHeader.setAttribute('aria-expanded', true);
		imtDetailHeader.setAttribute('aria-controls', `eventDetail${ei}`);
		const imtDetailCollapsed = DManip.createElement('div',
			['collapse', 'no-transition', 'border-bottom', 'event-detail', (requestsCount === 1 && (e.type === 'request' || e.type === 'query')) ? 'show' : '']);
		imtDetailCollapsed.setAttribute('aria-labelledby', `eventHeader${ei}`);
		imtDetailCollapsed.setAttribute('id', `eventDetail${ei}`);
		const imtDetailContent = DManip.createElement('div', ['card-body', 'p-0']);
		imtDetailHeader.innerHTML = `<div class="d-flex"><div class="my-auto"><i class="fas fa-caret-right fa-fw"></i></div></div>`;
		if (e.type === 'request') {
			imtDetailHeader.innerHTML += `
			<div class="pl-1 font-weight-bold">
				Request
			</div>
			<div class="pl-3 font-italic text-secondary text-truncate">
				${e.url}
			</div>
			`;
			const generateCURL = DManip.createElement('button', ['detail-header-button', 'py-0', 'px-1'], 'Copy cURL');
			generateCURL.setAttribute('type', 'button');
			generateCURL.addEventListener('click', () => {
				Exporter.copyStringToClipboard(Exporter.generateCURL(e));
			});
			const copyData = DManip.createElement('button', ['ml-auto', 'detail-header-button', 'py-0', 'px-1', 'mr-1'], 'Copy RAW');
			copyData.setAttribute('type', 'button');
			copyData.addEventListener('click', () => {
				Exporter.copyStringToClipboard(Exporter.generateRawReport(e));
			});
			imtDetailHeader.appendChild(copyData);
			imtDetailHeader.appendChild(generateCURL);
			imtDetailContent.appendChild(DManip.makeRequestTabs(e, `SD${ei}`));
		} else if (e.type === 'response') {
			imtDetailHeader.innerHTML += `
			<div class="pl-1 font-weight-bold">
				Response
			</div>
			<div class="pl-3 font-italic text-secondary text-truncate">
				Response without preceding request
			</div>
			`;
			imtDetailContent.appendChild(DManip.makeResponseTabs(e, `SD${ei}`));
		} else if (e.type === 'result') {
			imtDetailHeader.innerHTML += `
			<div class="pl-1 font-weight-bold">
				Result
			</div>
			<div class="pl-3 font-italic text-secondary text-truncate">
				Result without preceding query
			</div>
			`;
			imtDetailContent.appendChild(DManip.makeResultTabs(e, `SD${ei}`));
		} else if (e.type === 'message') {
			imtDetailHeader.innerHTML += `
			<div class="pl-1 font-weight-bold">
			Message
			</div>
			<div class="pl-3 font-italic text-secondary text-truncate">
				${e.args.map(arg => common.escapeHtml(arg)).join(', ')}
			</div>
			`;
			imtDetailContent.appendChild(DManip.makeMessageTab(e));
		} else if (e.type === 'query') {
			imtDetailHeader.innerHTML += `
			<div class="pl-1 font-weight-bold">
			Query
			</div>
			<div class="pl-3 font-italic text-secondary text-truncate">
				${e.command}
			</div>
			`;
			imtDetailContent.appendChild(DManip.makeQueryTabs(e, `SD${ei}`));
		} else if (e.type === 'profile') {
			imtDetailHeader.innerHTML += `
			<div class="pl-1 font-weight-bold">
				Profile
			</div>
			<div class="pl-3 font-italic text-secondary text-truncate">
				${e.name}, ${e.duration} ms
			</div>
			`;
			imtDetailContent.appendChild(DManip.makeProfileTab(e));
		} else if (e.type === 'error') {
			if (e.error) {
				imtDetailHeader.innerHTML += `
				<div class="pl-1 font-weight-bold">
					Error
				</div>
				<div class="pl-3 font-italic text-secondary text-truncate">
					${e.error.name} - ${common.escapeHtml(e.error.message)}
				</div>
				`;
				imtDetailContent.appendChild(DManip.makeErrorTab(e.error));
			} else {
				imtDetailHeader.innerHTML += `
				<div class="pl-1 font-weight-bold">
					Error
				</div>
				<div class="pl-3 font-italic text-secondary text-truncate">
					General Error
				</div>
				`;
				imtDetailContent.appendChild(DManip.makePlainEditorTab(e));
			}
		}
		if (requestsCount === 1 && (e.type === 'request' || e.type === 'query')) {
			const caret = imtDetailHeader.getElementsByClassName('fas')[0];
			caret.classList.remove('fa-caret-right');
			imtDetailContent.classList.remove('hide');
			DManip.refreshMirrors();
			caret.classList.add('fa-caret-down');
		}
		imtDetail.appendChild(imtDetailHeader);
		imtDetailCollapsed.appendChild(imtDetailContent);
		imtDetail.appendChild(imtDetailCollapsed);
		eventListItems.appendChild(imtDetail);
	});
	// jQuery handlers for collapsing, showing and the important part - refreshing CodeMirror blocks
	$('.collapse.event-detail').on('show.bs.collapse', (e) => {
		const caret = document.getElementById(e.target.getAttribute('aria-labelledby')).getElementsByClassName('fas')[0];
		caret.classList.remove('fa-caret-right');
		caret.classList.add('fa-caret-down');
	});
	$('.collapse.event-detail').on('hide.bs.collapse', (e) => {
		const caret = document.getElementById(e.target.getAttribute('aria-labelledby')).getElementsByClassName('fas')[0];
		caret.classList.remove('fa-caret-down');
		caret.classList.add('fa-caret-right');
	});
	$('.collapse.event-detail').on('shown.bs.collapse', () => {
		DManip.refreshMirrors();
	});
	$('.collapse.event-detail').on('shown.bs.tab', () => {
		DManip.refreshMirrors();
	});
	$('.detail-header-button').on('click', (ev) => {
		ev.stopPropagation();
	});
	// Executes the global injected functions for initializing all the CodeMirrors
	window.mirrorify();
}
