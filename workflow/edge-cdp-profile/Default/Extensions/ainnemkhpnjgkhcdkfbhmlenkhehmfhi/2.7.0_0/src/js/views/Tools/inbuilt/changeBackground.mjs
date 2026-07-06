export default {
    icon: 'far fa-fill-drip',
    name: 'changeBackground',
    label: 'Change Background',
    description: `Temporarily changes the background color of the scenario.
	This is useful for example when you need a purely white background for screenshots and mockups.
	To <strong>reset</strong> background, refresh the browser window.`,
    theme: '#61beed',
    input: [{
        name: 'color',
        label: 'New Background Color',
        type: 'color',
        default: '#ffffff',
        help: 'The new color to be set as the background color.',
        mappable: true,
        required: true
    }],
    steps: [{
        type: 'javascript',
        code: `document.body.style.backgroundColor = parameters.color;`
    }]
};