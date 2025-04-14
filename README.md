# roguelike.club

Put web stuff in `docs/`.

A previous version of this README noted this code was based on <https://v4-alpha.getbootstrap.com/examples/cover/>. I can no longer confirm or deny how much that's still the case ~6 years later.

## Deployment

The website is automatically deployed whenever new commits are pushed to the `main` branch via GitHub Pages.

A note for future maintainers: the `docs` folder was previously called `public`, but GH Pages will only let you deploy the root folder or the "docs" folder. Eventually, we could set up a GitHub Actions script to auto-deploy an arbitrary folder to another branch, but that seems like overkill as long as this remains static HTML with no need for a pre-processing/compilation step.
