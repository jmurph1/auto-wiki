# scripts/update_wiki.py
import os
import shutil
import sys
from pathlib import Path # For using Path objects with pydoc-markdown

# --- pydoc-markdown Library Imports ---
from pydoc_markdown import PydocMarkdown, PythonLoader
from pydoc_markdown.contrib.processors import SmartProcessor # A common and useful processor
# You might want to import other processors if you used them in your YAML, e.g.:
# from pydoc_markdown.contrib.processors.filter import FilterProcessor
from pydoc_markdown.contrib.renderers.markdown import MarkdownRenderer, PagesType

# --- Configuration ---
# MAIN_REPO_ROOT will be the current working directory when the script is run from main_repo in GHA
MAIN_REPO_ROOT = os.getcwd()
# PYDOC_OUTPUT_DIR is where pydoc-markdown will generate the Markdown files
PYDOC_OUTPUT_DIR = os.path.join(MAIN_REPO_ROOT, "pydoc_generated_docs")
# WIKI_API_SUBDIR is the subdirectory in your GitHub Wiki where the generated API docs will be placed
WIKI_API_SUBDIR = "api"


def run_pydoc_markdown_programmatic():
    """
    Configures and runs pydoc-markdown programmatically to generate Markdown documentation.
    """
    print(f"Starting programmatic pydoc-markdown generation...")
    print(f"Source code (search_path) expected relative to: {MAIN_REPO_ROOT}")
    print(f"Temporary Markdown output will be in: {Path(PYDOC_OUTPUT_DIR).resolve()}")

    # Ensure the temporary output directory for pydoc-markdown is clean before generation.
    # The renderer itself will create the directory.
    if os.path.exists(PYDOC_OUTPUT_DIR):
        print(f"Cleaning up existing temporary output directory: {PYDOC_OUTPUT_DIR}")
        shutil.rmtree(PYDOC_OUTPUT_DIR)

    # Initialize PydocMarkdown
    pm = PydocMarkdown()

    # 1. Configure Loaders
    # This tells pydoc-markdown where to find your Python source code.
    # Adjust 'search_path' if your code is not in a 'src' directory at the repo root.
    # For example, if your package 'my_package' is directly at the root: search_path=["my_package"]
    # Or, to be very specific about packages: pm.loaders = [PythonLoader(packages=["my_package_name"])]
    pm.loaders = [
        PythonLoader(search_path=["src"])  # IMPORTANT: Ensure 'src' contains your Python package(s)
    ]

    # 2. Configure Processors
    # Processors modify the documentation data after loading.
    # SmartProcessor is good for inferring titles and TOCs.
    pm.processors = [
        SmartProcessor(),
        # Add other processors if needed, e.g., for filtering:
        # FilterProcessor(skip_empty_modules=True, documented_only=True)
    ]

    # 3. Configure Renderer
    # This is where you define how the Markdown is generated.
    pm.renderer = MarkdownRenderer(
        # --- Core Parameters for Output and Structure ---
        output_directory=Path(PYDOC_OUTPUT_DIR), # Must be a pathlib.Path object
        pages_type=PagesType.MODULE,             # Generates one .md file per module

        # --- Fine-tuning Markdown Output (adjust as per your preference) ---
        render_module_header=False, # Set to True if you want "Module `module_name`" headers
        render_toc=True,            # Set to True to include a Table of Contents in each module file
        descriptive_toc=False,      # Set to True for more descriptive TOC entries (default is False)
        # filename_suffix=".md",    # Default is ".md"
        # ... explore other MarkdownRenderer parameters if needed ...
    )

    print("pydoc-markdown configured. Starting .render() process...")
    try:
        pm.render()
        print("pydoc-markdown .render() completed successfully.")
        if not os.path.exists(PYDOC_OUTPUT_DIR) or not os.listdir(PYDOC_OUTPUT_DIR):
            print(f"Warning: pydoc-markdown .render() completed but '{PYDOC_OUTPUT_DIR}' is missing or empty.")
        else:
            print(f"Generated files in '{PYDOC_OUTPUT_DIR}': {os.listdir(PYDOC_OUTPUT_DIR)}")
            
    except Exception as e:
        print(f"Error during pydoc-markdown pm.render(): {type(e).__name__} - {e}")
        # Uncomment for more detailed traceback during debugging:
        # import traceback
        # traceback.print_exc()
        raise # Re-raise the exception to fail the script if render fails


def clear_wiki_api_directory(wiki_repo_path: str):
    """Clears the WIKI_API_SUBDIR in the wiki to remove stale auto-generated files."""
    wiki_api_path = os.path.join(wiki_repo_path, WIKI_API_SUBDIR)
    print(f"Clearing wiki API directory: {wiki_api_path}")
    if os.path.exists(wiki_api_path):
        shutil.rmtree(wiki_api_path)
    os.makedirs(wiki_api_path, exist_ok=True) # Ensure directory exists for copying


def copy_generated_docs_to_wiki(wiki_repo_path: str) -> list[str]:
    """
    Copies generated Markdown files from PYDOC_OUTPUT_DIR to the wiki's API subdirectory.
    Returns a list of copied markdown file names (without path).
    """
    wiki_api_target_path = os.path.join(wiki_repo_path, WIKI_API_SUBDIR)
    print(f"Copying generated docs from '{PYDOC_OUTPUT_DIR}' to '{wiki_api_target_path}'...")

    if not os.path.exists(PYDOC_OUTPUT_DIR):
        print(f"Error: pydoc-markdown output directory '{PYDOC_OUTPUT_DIR}' not found. No docs to copy.")
        return []

    copied_file_names = []
    # Ensure PYDOC_OUTPUT_DIR itself is not empty
    if not os.listdir(PYDOC_OUTPUT_DIR):
        print(f"Warning: pydoc-markdown output directory '{PYDOC_OUTPUT_DIR}' is empty.")
        return []

    for item_name in os.listdir(PYDOC_OUTPUT_DIR):
        source_item_path = os.path.join(PYDOC_OUTPUT_DIR, item_name)
        if os.path.isfile(source_item_path) and item_name.endswith(".md"):
            target_item_path = os.path.join(wiki_api_target_path, item_name)
            shutil.copy2(source_item_path, target_item_path)
            copied_file_names.append(item_name)
            print(f"Copied: {item_name} to {wiki_api_target_path}")
    
    if not copied_file_names:
        print("No .md files were found in the pydoc-markdown output to copy.")
    return copied_file_names


def generate_wiki_home(wiki_repo_path: str, module_file_names: list[str]):
    """Generates Home.md with a list of documented modules."""
    home_md_path = os.path.join(wiki_repo_path, "Home.md")
    print(f"Generating {home_md_path}...")

    content = "# Project Documentation\n\n"
    content += "Welcome to the project documentation wiki. This wiki is auto-generated from the Google-style docstrings in the Python code.\n\n"
    content += "## API Modules\n\n"

    if module_file_names:
        for module_filename in sorted(module_file_names): # Sort for consistent order
            module_name = module_filename[:-3] # Remove .md extension
            # Link to the page within the WIKI_API_SUBDIR
            content += f"* [{module_name}]({WIKI_API_SUBDIR}/{module_filename})\n"
    else:
        content += "No API modules have been documented yet, or no documentation files were generated.\n"

    with open(home_md_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"{home_md_path} generated.")


def generate_wiki_sidebar(wiki_repo_path: str, module_file_names: list[str]):
    """Generates _Sidebar.md with a list of documented modules for wiki navigation."""
    sidebar_md_path = os.path.join(wiki_repo_path, "_Sidebar.md")
    print(f"Generating {sidebar_md_path}...")

    # Sidebar content often starts with a link to Home
    content = f"* [Home](Home.md)\n\n**API Modules**\n\n"
    if module_file_names:
        for module_filename in sorted(module_file_names): # Sort for consistent order
            module_name = module_filename[:-3] # Remove .md extension
            # Link to the page within the WIKI_API_SUBDIR
            content += f"* [{module_name}]({WIKI_API_SUBDIR}/{module_filename})\n"
    else:
        content += "No API modules documented.\n"

    with open(sidebar_md_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"{sidebar_md_path} generated.")


def main(wiki_repo_abs_path: str):
    """Main function to orchestrate the wiki generation process."""
    print(f"Starting wiki update process. Wiki repo absolute path: {wiki_repo_abs_path}")
    
    # 1. Generate Markdown from source code using pydoc-markdown programmatically
    # This will output files to PYDOC_OUTPUT_DIR
    try:
        run_pydoc_markdown_programmatic()
    except Exception as e:
        print(f"Halting script due to error in pydoc-markdown generation: {e}")
        sys.exit(1) # Exit if pydoc generation fails

    # 2. Clear the target API directory in the wiki (e.g., wiki_repo/api/)
    clear_wiki_api_directory(wiki_repo_abs_path)

    # 3. Copy newly generated docs to the wiki's API subdirectory
    #    and get a list of the generated module markdown file names.
    generated_md_files = copy_generated_docs_to_wiki(wiki_repo_abs_path)

    if not generated_md_files:
        print("Warning: No module documentation files were copied to the wiki. Home.md and _Sidebar.md will reflect this.")
    
    # 4. Generate Home.md for the wiki
    generate_wiki_home(wiki_repo_abs_path, generated_md_files)

    # 5. Generate _Sidebar.md for the wiki
    generate_wiki_sidebar(wiki_repo_abs_path, generated_md_files)

    print("Wiki generation script finished successfully.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python update_wiki.py <absolute_path_to_wiki_repo_checkout>")
        print("Example: python scripts/update_wiki.py \"${{ github.workspace }}/wiki_repo\"")
        sys.exit(1)
    
    # The GitHub Action will provide an absolute path to the wiki_repo checkout
    # (e.g., /home/runner/work/my-repo/my-repo/wiki_repo)
    wiki_checkout_path_arg = sys.argv[1]
    
    # Perform a basic check on the path
    if not os.path.isdir(wiki_checkout_path_arg):
        print(f"Error: Provided wiki repo path is not a valid directory: {wiki_checkout_path_arg}")
        sys.exit(1)
        
    main(wiki_checkout_path_arg)