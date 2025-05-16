# scripts/update_wiki.py
import os
import shutil
import subprocess
import glob
import sys

# --- Configuration ---
# These paths will be relative to the root of the main_repo checkout in GitHub Actions
MAIN_REPO_ROOT = os.getcwd() # Script is expected to be run from the root of main_repo
PYDOC_CONFIG_FILE = os.path.join(MAIN_REPO_ROOT, "pydoc-markdown.yml")
PYDOC_OUTPUT_DIR = os.path.join(MAIN_REPO_ROOT, "pydoc_generated_docs") # Matches renderer.output_directory

# These paths will be relative to where the script is run, but point to the checked-out locations
# We'll receive the wiki repo path as an argument for clarity
# WIKI_REPO_PATH comes from GHA workflow: ../wiki_repo relative to main_repo
# So, if script is in main_repo/scripts, WIKI_REPO_PATH would be ../../wiki_repo from script's perspective

WIKI_API_SUBDIR = "api" # Subdirectory in the wiki for generated module docs

def run_pydoc_markdown():
    """Runs pydoc-markdown to generate Markdown files."""
    print("Running pydoc-markdown...")

    # ---- Start: Verify pydoc-markdown executable ----
    pydoc_executable_path = shutil.which("pydoc-markdown")
    if not pydoc_executable_path:
        print("CRITICAL ERROR: pydoc-markdown command not found in PATH.")
        raise FileNotFoundError("pydoc-markdown command not found. Ensure it's installed and on the PATH.")
    
    print(f"Found pydoc-markdown executable at: {pydoc_executable_path}")
    
    # Check if the path seems to be the pipx one (this is a heuristic)
    home_dir = os.path.expanduser("~")
    expected_pipx_path_fragment_1 = os.path.join(home_dir, ".local", "bin", "pydoc-markdown")
    expected_pipx_path_fragment_2 = os.path.join(home_dir, ".pyenv", "shims", "pydoc-markdown") # If pyenv is used with pipx
    expected_pipx_path_fragment_3 = "pipx/bin/pydoc-markdown" # Another common pipx structure

    if not (pydoc_executable_path == expected_pipx_path_fragment_1 or \
            pydoc_executable_path == expected_pipx_path_fragment_2 or \
            expected_pipx_path_fragment_3 in pydoc_executable_path):
        print(f"WARNING: The pydoc-markdown executable at '{pydoc_executable_path}' "
              f"might not be the one installed by pipx into '{expected_pipx_path_fragment_1}' or similar. "
              "This could lead to version or configuration mismatches.")
    # ---- End: Verify pydoc-markdown executable ----

    try:
        # Ensure the output directory for pydoc-markdown is clean or non-existent
        if os.path.exists(PYDOC_OUTPUT_DIR):
            shutil.rmtree(PYDOC_OUTPUT_DIR)

        print(f"Executing: {pydoc_executable_path} {PYDOC_CONFIG_FILE} from cwd: {MAIN_REPO_ROOT}")
        process = subprocess.run(
            [pydoc_executable_path, PYDOC_CONFIG_FILE], # Use the resolved absolute path
            check=True,
            capture_output=True,
            text=True,
            cwd=MAIN_REPO_ROOT
        )
        print("pydoc-markdown execution successful.")
        if process.stdout:
            print(f"pydoc-markdown stdout:\n{process.stdout}")
        # Warnings from pydoc-markdown go to stderr, so always print it if it exists.
        if process.stderr:
            print(f"pydoc-markdown stderr:\n{process.stderr}")

    except subprocess.CalledProcessError as e:
        print(f"Error during pydoc-markdown execution (CalledProcessError):")
        print(f"  Command: {' '.join(e.cmd)}")
        print(f"  Return code: {e.returncode}")
        print(f"  Stdout:\n{e.stdout}")
        print(f"  Stderr:\n{e.stderr}")
        raise
    except FileNotFoundError: # Should be caught by shutil.which check now, but good for defense
        print(f"CRITICAL ERROR: Failed to find pydoc-markdown executable at '{pydoc_executable_path}'.")
        raise
    except Exception as e:
        print(f"An unexpected error occurred during pydoc-markdown execution: {e}")
        raise

def clear_wiki_api_directory(wiki_repo_path):
    """Clears the WIKI_API_SUBDIR in the wiki to remove stale files."""
    wiki_api_path = os.path.join(wiki_repo_path, WIKI_API_SUBDIR)
    print(f"Clearing wiki API directory: {wiki_api_path}")
    if os.path.exists(wiki_api_path):
        shutil.rmtree(wiki_api_path)
    os.makedirs(wiki_api_path, exist_ok=True)

def copy_generated_docs_to_wiki(wiki_repo_path):
    """Copies generated Markdown files from PYDOC_OUTPUT_DIR to the wiki's API subdirectory."""
    wiki_api_path = os.path.join(wiki_repo_path, WIKI_API_SUBDIR)
    print(f"Copying generated docs from {PYDOC_OUTPUT_DIR} to {wiki_api_path}...")

    if not os.path.exists(PYDOC_OUTPUT_DIR):
        print(f"Error: pydoc-markdown output directory '{PYDOC_OUTPUT_DIR}' not found. No docs to copy.")
        return [] # Return empty list if no docs generated

    copied_module_files = []
    for item_name in os.listdir(PYDOC_OUTPUT_DIR):
        source_item_path = os.path.join(PYDOC_OUTPUT_DIR, item_name)
        if os.path.isfile(source_item_path) and item_name.endswith(".md"):
            target_item_path = os.path.join(wiki_api_path, item_name)
            shutil.copy2(source_item_path, target_item_path)
            copied_module_files.append(item_name)
            print(f"Copied: {item_name}")
    
    if not copied_module_files:
        print("No .md files found in pydoc-markdown output to copy.")
    return copied_module_files


def generate_wiki_home(wiki_repo_path, module_files):
    """Generates Home.md with a list of documented modules."""
    home_md_path = os.path.join(wiki_repo_path, "Home.md")
    print(f"Generating {home_md_path}...")

    content = "# Project Documentation\n\n"
    content += "Welcome to the project documentation wiki. This wiki is auto-generated from the Google-style docstrings in the Python code.\n\n"
    content += "## Modules\n\n"

    if module_files:
        for module_file in sorted(module_files):
            module_name = module_file.replace(".md", "")
            # Link to the page in the api subdirectory
            content += f"* [{module_name}]({WIKI_API_SUBDIR}/{module_file})\n"
    else:
        content += "No modules have been documented yet.\n"

    with open(home_md_path, "w") as f:
        f.write(content)
    print(f"{home_md_path} generated.")

def generate_wiki_sidebar(wiki_repo_path, module_files):
    """Generates _Sidebar.md with a list of documented modules."""
    sidebar_md_path = os.path.join(wiki_repo_path, "_Sidebar.md")
    print(f"Generating {sidebar_md_path}...")

    content = "**Modules**\n\n"
    if module_files:
        for module_file in sorted(module_files):
            module_name = module_file.replace(".md", "")
            # Link to the page in the api subdirectory
            content += f"* [{module_name}]({WIKI_API_SUBDIR}/{module_file})\n"
    else:
        content += "No modules documented.\n"

    with open(sidebar_md_path, "w") as f:
        f.write(content)
    print(f"{sidebar_md_path} generated.")

def main(wiki_repo_abs_path):
    print(f"Starting wiki update process. Wiki repo path: {wiki_repo_abs_path}")
    
    # 1. Generate Markdown from source code using pydoc-markdown
    run_pydoc_markdown()

    # 2. Clear the target API directory in the wiki
    clear_wiki_api_directory(wiki_repo_abs_path)

    # 3. Copy newly generated docs to the wiki's API subdirectory
    #    and get a list of the generated module markdown file names.
    generated_module_md_files = copy_generated_docs_to_wiki(wiki_repo_abs_path)

    if not generated_module_md_files:
        print("No module documentation was generated or copied. Home.md and _Sidebar.md will reflect this.")
    
    # 4. Generate Home.md
    generate_wiki_home(wiki_repo_abs_path, generated_module_md_files)

    # 5. Generate _Sidebar.md
    generate_wiki_sidebar(wiki_repo_abs_path, generated_module_md_files)

    print("Wiki generation script finished.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python update_wiki.py <path_to_wiki_repo>")
        sys.exit(1)
    
    # The GitHub Action will provide an absolute path to the wiki_repo checkout
    wiki_path_arg = sys.argv[1]
    main(wiki_path_arg)