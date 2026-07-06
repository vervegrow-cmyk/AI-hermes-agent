import handlers from './handlers.mjs';
import * as actions from './actions.mjs';
import * as helpers from './helpers.mjs';
import * as ChromeAsync from '../../../lib/ChromeAsync.mjs';

import { default as template } from './template.mjs';
export const config = {
    id: 'tools',
    name: 'Tools',
    sidebarIcon: ['far', 'fa-fw', 'fa-toolbox'],
    template: template
};

// === TOOLS CONFIGURATION HERE
import focusModule from './inbuilt/focusModule.mjs';
import searchByConfig from './inbuilt/searchByConfig.mjs';
import swapVariable from './inbuilt/swapVariable.mjs';
import swapConnection from './inbuilt/swapConnection.mjs';
import getAppMetadata from './inbuilt/getAppMetadata.mjs';
import swapApp from './inbuilt/swapApp.mjs';
import copyMapping from './inbuilt/copyMapping.mjs';
import copyFilter from './inbuilt/copyFilter.mjs';
import base64 from './inbuilt/base64.mjs';
import remapSource from './inbuilt/remapSource.mjs';
import copyModuleName from './inbuilt/copyModuleName.mjs';
import highlightApp from './inbuilt/highlightApp.mjs';
import showcaseMode from './inbuilt/showcaseMode.mjs';
import showcaseNames from './inbuilt/showcaseNames.mjs';
import changeBackground from './inbuilt/changeBackground.mjs';
import getBlueprintSize from './inbuilt/getBlueprintSize.mjs';

const tools = [
    focusModule,
    searchByConfig,
    getAppMetadata,
    copyMapping,
    copyFilter,
    swapConnection,
    swapVariable,
    swapApp,
    base64,
    copyModuleName,
    remapSource,
    highlightApp,
	getBlueprintSize,
    showcaseMode,
    showcaseNames,
    changeBackground,
];
// === END OF TOOLS CONFIGURATION

const lastActive = { tool: null, toolColor: null, hiddenTools: [] };

/**
 * Main initializer function
 * @param {extercomm} extercomm Extercomm instance to use
 */
export async function init(extercomm) {
    document.getElementById('toolsSearch').addEventListener('keyup', () => { helpers.toolsSearch(lastActive) });
    document.getElementById('toolsOpenHelp').addEventListener('click', async() => {
        await ChromeAsync.openTab(`https://www.make.com/en/help/scenarios/make-devtool#tools-935227`);
    });
    actions.drawTools(extercomm, tools, lastActive);
}

/**
 * Handler registering function
 * @param {extercomm} extercomm Extercomm instance to use
 * @param {object} meta Metadata from the upper scope
 * @param {function} focusSelf Focus self with binded context to focus the pane
 */
export async function registerHandlers(extercomm, meta, focusSelf) {
    handlers.forEach(handler => {
        extercomm.addEventListener(handler.event, async(e) => {
            if (meta.initiated !== true && handler.shouldBeInitiatedBefore) {
                await init(extercomm);
                meta.initiated = true;
            }
            if (handler.shouldFocus) {
                focusSelf();
            }
            handler.execute(e, extercomm, lastActive, tools);
        });
    });
}
