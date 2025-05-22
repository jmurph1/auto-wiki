# auto-wiki
Automatically generate Python documentation for any Github repo. The current implementation uses the ['pydoc-markdown'](https://github.com/NiklasRosenstein/pydoc-markdown) tool to synthesize all Python docstrings (any style, e.g. Google, Sphinx, etc.) found in a directory into an organized Markdown file. The workflow then pushes the changes directly to the Github native wiki for your repo.

## Notes: 
1. Github offers a free native wiki for any *public* repo. (A paid Github account is required to enable the wiki in private repos.)
2. To enable the native wiki for a repo, you must have admin privileges for that repo.
3. To instantiate the wiki, simply go to the **'Settings'** tab in the main toolbar (the toolbar directly below the Github icon/ your username, etc.), scroll down a bit and you should see it as the first item under **'Features'**.
4. The wiki tab will then appear on the toolbar, whereupon you must click into it, then create the first page with the green button. (This has to be done before the workflow is run for the first time.)
5. Simply pushing the workflow into the main branch will cause it to be run for the first time, and it will populate the wiki. (If you'd like to test the output first, just add a different branch name to the beginning of the workflow next to 'main'.)
