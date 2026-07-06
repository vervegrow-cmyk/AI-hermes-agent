import * as DManip from '../../../lib/DManip.mjs';
import * as Exporter from '../../../lib/Exporter.mjs';

/**
 * @description Draws a detailed event view to the detail pane
 * @param {object} detail Detail to show
 * @param {nubmer} index Index to generate unique identifier
 */
export async function showEventDetail(detail, index) {
	const liveStreamDetails = document.getElementById('livestreamDetails');
	liveStreamDetails.innerHTML = '';
	const liveStreamDetailWrapper = DManip.createElement('div', ['p-0', 'm-0', 'livestream-detail', 'card-body', 'row']);
	const liveStreamDetail = DManip.createElement('div', ['p-0', 'col']);
	// Generate correct content based on type
	switch (detail.type) {
		case 'request':
			const imtDetailHeader = DManip.createElement('div', ['card-header', 'd-flex', 'py-1', 'pl-2', 'pr-1', 'border-bottom']);
			imtDetailHeader.innerHTML = `<div class="d-flex"><div class="my-auto"></div></div>
			<div class="text-secondary">
				Request tools
			</div>`;
			const generateCURL = DManip.createElement('button', ['detail-header-button', 'py-0', 'px-1'], 'Copy cURL');
			generateCURL.setAttribute('type', 'button');
			generateCURL.addEventListener('click', () => {
				Exporter.copyStringToClipboard(Exporter.generateCURL(detail));
			});
			const copyData = DManip.createElement('button', ['ml-auto', 'detail-header-button', 'py-0', 'px-1', 'mr-1'], 'Copy RAW');
			copyData.setAttribute('type', 'button');
			copyData.addEventListener('click', () => {
				Exporter.copyStringToClipboard(Exporter.generateRawReport(detail));
			});
			imtDetailHeader.appendChild(copyData);
			imtDetailHeader.appendChild(generateCURL);
			liveStreamDetail.appendChild(imtDetailHeader);
			liveStreamDetail.appendChild(DManip.makeRequestTabs(detail, `LS${index}`));
			break;
		case 'message':
			liveStreamDetail.appendChild(DManip.makeMessageTab(detail));
			break;
		case 'query':
			liveStreamDetail.appendChild(DManip.makeQueryTabs(detail, `LS${index}`));
			break;
		case 'profile':
			liveStreamDetail.appendChild(DManip.makeProfileTab(detail));
			break;
		case 'response':
			liveStreamDetail.appendChild(DManip.makeResponseTabs(detail, `LS${index}`));
			break;
		case 'result':
			liveStreamDetail.appendChild(DManip.makeResultTabs(detail, `LS${index}`));
			break;
		case 'error':
			if (detail.error) {
				liveStreamDetail.appendChild(DManip.makeErrorTab(detail.error));
				break;
			} else {
				liveStreamDetail.appendChild(DManip.makePlainEditorTab(detail));
				break;
			}
	}
	liveStreamDetailWrapper.appendChild(liveStreamDetail);
	liveStreamDetails.appendChild(liveStreamDetailWrapper);
	// jQuery hook to refresh mirrors correctly on tabs switch
	$('.livestream-detail').on('shown.bs.tab', () => {
		DManip.refreshMirrors();
	});
}
