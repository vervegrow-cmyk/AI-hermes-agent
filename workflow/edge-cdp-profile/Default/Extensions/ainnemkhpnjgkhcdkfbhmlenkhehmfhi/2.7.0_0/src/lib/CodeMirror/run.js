window.editors = [];
window.mirrorify = () => {
	const codeViews = document.getElementsByClassName('code-view');
	for (const cv of codeViews) {
		if (!cv.classList.contains('mirrorified')) {
			// eslint-disable-next-line no-undef
			window.editors.push(CodeMirror.fromTextArea(cv, {
				mode: 'javascript',
				lineNumbers: true,
				lineWrapping: true,
				readOnly: 'true',
				viewportMargin: Infinity,
				foldGutter: true,
				gutters: ['CodeMirror-linenumbers', 'CodeMirror-foldgutter']
			}));
			cv.classList.add('mirrorified');
		}
	}
	const codeEdits = document.getElementsByClassName('code-edit');
	for (const ce of codeEdits) {
		if (!ce.classList.contains('mirrorified')) {
			let e;
			if (ce.classList.contains('yaml-editor')) {
				// eslint-disable-next-line no-undef
				e = CodeMirror.fromTextArea(ce, {
					mode: 'yaml',
					lineNumbers: true,
					lineWrapping: true,
					viewportMargin: Infinity,
					foldGutter: true,
					lint: true,
					gutters: ['CodeMirror-linenumbers', 'CodeMirror-foldgutter', 'CodeMirror-lint-markers']
				});
			} else {
				// eslint-disable-next-line no-undef
				e = CodeMirror.fromTextArea(ce, {
					mode: 'javascript',
					lineNumbers: true,
					lineWrapping: true,
					viewportMargin: Infinity,
					foldGutter: true,
					gutters: ['CodeMirror-linenumbers', 'CodeMirror-foldgutter']
				});
			}
			if (ce.id === 'tool-edit') {
				window.currentToolEdit = e;
			}
			window.editors.push(e);
			ce.classList.add('mirrorified');
		}
	}
};
