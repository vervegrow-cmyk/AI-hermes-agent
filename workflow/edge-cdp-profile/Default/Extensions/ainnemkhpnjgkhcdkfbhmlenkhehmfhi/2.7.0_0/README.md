# Chrome Make DevTool

# Branding

## Colors and logo

All bundled assets are stored in `/src/static/*`.


Color scheme is controled by Bootstrap.
If a change of the color scheme is needed, the file `/src/static/css/bootstrap4.min.css` has to be updated.

Logo is stored in `src/static/img/logo-light.svg`.
You can change the displayed logo by replacing this file.

## Font Awesome

Because of the license, the FontAwesome **can't be embedded into the DevTool** and it has to be loaded directly from the **Instance**.
You can change the source of FontAwesome in `src/html/index.html` file in the link in the `<head>` section.
Also you might need to change the `content_security_policy` string in the `mainfest.json` file to allow loading FA from a custom target.
