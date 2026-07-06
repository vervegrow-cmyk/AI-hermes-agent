# eBay Listing HTML Workflow

## Purpose

This workflow fixes the structure that performed well in eBay preview:

- full-width outer layout
- no narrow centered content box
- inline CSS only
- first 1-2 poster images displayed as standalone sections
- later detail images converted into alternating text-image modules
- compact specs, package, FAQ, use note, and shipping sections

## Best structure

1. Header
2. Key features table
3. Quick product summary
4. Poster image 1
5. Poster image 2
6. Detail module 1
7. Detail module 2
8. Detail module 3
9. Detail module 4
10. Detail module 5
11. Detail module 6
12. Specifications
13. Suitable For + Package Includes
14. FAQ
15. Use Note
16. Shipping & Service

## Image placement logic

### Put first

Use strong composite graphics or poster boards first when they:

- summarize the product
- show multiple selling points at once
- already look like a hero board

### Put later

Use clean product shots, close-ups, and scenario images in detail modules when they:

- show a specific feature
- show a part or material
- show fit, scale, package, or use scenario

## Copy logic

Each detail module should contain:

- one small uppercase kicker
- one clear benefit-led title
- one paragraph explaining the feature
- one paragraph explaining where or why it helps

## GEO writing pattern

Use the main product phrase naturally in:

- title
- subtitle
- summary block
- at least 2 module titles
- specs or FAQ when relevant

Also cover:

- target user
- scenario
- function
- material or size
- charging or power method

## Risk handling

If image text conflicts with provided facts:

- warn in material analysis
- remove the conflicting claim from written copy
- use the image only if the user explicitly wants all uploaded images included

## eBay paste notes

- The generated HTML should be pasted into `Show HTML Code`
- Avoid extra wrapper widths like `max-width:900px;margin:0 auto;` when the eBay container already narrows the content
- Use `width:100%;margin:0;padding:0;` on the outside
