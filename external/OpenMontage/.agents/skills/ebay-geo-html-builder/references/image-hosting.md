# ImgBB Image Hosting

## Use Cases

Use ImgBB support when:
- the HTML still points at local filesystem image paths
- the user wants public image URLs for eBay or a marketplace editor
- the user wants a quick hosted-image pass without manually uploading every file

## Preferred Workflow

### Upload standalone images

Use `scripts/upload_to_imgbb.py` for:
- one image
- an entire folder
- generating a JSON manifest of local path to public URL

### Rewrite HTML image sources

Use `scripts/upload_html_images_to_imgbb.py` for:
- scanning HTML for `<img src="...">`
- uploading local image files automatically
- rewriting the HTML with public ImgBB URLs

## Scope Rules

Only upload images that are local files:
- absolute Windows paths
- relative paths that resolve from the HTML file directory

Do not re-upload:
- `http://`
- `https://`
- `data:`
- protocol-relative URLs

## Output Guidance

When rewriting HTML, prefer writing to a new file such as:
- `*-imgbb.html`
- `*-hosted.html`

When producing a manifest, keep:
- original local path
- public display URL
- delete URL if the API returns one

## Environment

These scripts expect `IMGBB_API_KEY`.

You can pass:
- `--env-file <path>`

or rely on the key already being present in the process environment.
