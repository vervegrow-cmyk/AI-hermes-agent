/**
 * @description Escapes HTML characters
 * @param {String} unsafe String containing HTML
 * @return {String} String with safe HTML entities
 */
export function escapeHtml(unsafe) {
	if (typeof unsafe !== 'string') return unsafe;
	return unsafe
		.replace(/&/g, "&amp;")
		.replace(/</g, "&lt;")
		.replace(/>/g, "&gt;")
		.replace(/"/g, "&quot;")
		.replace(/'/g, "&#039;");
}
