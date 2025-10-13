#!/usr/bin/env python3
"""
Generate documentation pages for public plugins from Supabase database.

This script fetches plugin data from the public_plugin view and generates:
1. Individual MDX pages for each plugin
2. A main overview page with a table of all plugins

Environment variables required:
- SUPABASE_URL: Your Supabase project URL
- SUPABASE_KEY: Your Supabase anon/service key

Usage:
    export SUPABASE_URL="https://your-project.supabase.co"
    export SUPABASE_KEY="your-key-here"
    python generate_plugin_docs.py
"""

import os
import json
import sys
from typing import List, Dict, Any
from pathlib import Path
import re
import yaml

# Load environment variables from .env file if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not installed, will rely on environment variables
    pass

try:
    from supabase import create_client, Client
except ImportError:
    print("Error: supabase package not found. Install with: pip install supabase")
    sys.exit(1)


def get_supabase_client() -> Client:
    """Initialize and return Supabase client."""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")

    if not url or not key:
        print("Error: SUPABASE_URL and SUPABASE_KEY environment variables must be set")
        sys.exit(1)

    return create_client(url, key)


def fetch_public_plugins(client: Client) -> List[Dict[str, Any]]:
    """Fetch all plugins from the public_plugin view."""
    try:
        response = client.table("public_plugin").select("*").execute()
        return response.data
    except Exception as e:
        print(f"Error fetching plugins from Supabase: {e}")
        sys.exit(1)


def sanitize_filename(name: str) -> str:
    """Convert plugin name to a valid filename."""
    # Convert to lowercase, replace spaces and special chars with hyphens
    filename = re.sub(r'[^\w\s-]', '', name.lower())
    filename = re.sub(r'[-\s]+', '-', filename)
    return filename.strip('-')


def save_icon_if_present(plugin: Dict[str, Any], output_dir: Path) -> str:
    """
    Save plugin icon to the images directory and return the path.
    Returns relative path to the icon or empty string if no icon.
    """
    if not plugin.get('icon'):
        return ""

    icon_data = plugin['icon']
    plugin_slug = sanitize_filename(plugin['name'])

    # Create images directory if it doesn't exist
    images_dir = output_dir.parent / "images" / "public-plugins"
    images_dir.mkdir(parents=True, exist_ok=True)

    # Determine file extension from icon data (if it's a URL or base64)
    # For now, assuming it's a URL or we'll save as .png
    # You may need to adjust this based on your actual icon format
    icon_filename = f"{plugin_slug}-icon.png"
    icon_path = images_dir / icon_filename

    # If icon is a URL, we'll just reference it
    # If it's base64 or binary data, we'd need to save it
    # For simplicity, we'll assume it's already accessible or a URL
    # Return the relative path for MDX
    return f"/images/public-plugins/{icon_filename}"


def generate_plugin_page(plugin: Dict[str, Any], output_dir: Path) -> str:
    """
    Generate an MDX page for a single plugin.
    Returns the filename (slug) of the generated page.
    """
    plugin_slug = sanitize_filename(plugin['name'])
    filename = f"{plugin_slug}.mdx"
    filepath = output_dir / filename

    # Extract metadata
    name = plugin.get('name', 'Unnamed Plugin')
    description = plugin.get('description', '')
    readme = plugin.get('readme', 'No documentation available.')
    icon = plugin.get('icon', '')

    # Build frontmatter using YAML library for proper escaping
    frontmatter_data = {
        'title': name,
        'description': description
    }

    # Don't add icon to frontmatter - it causes rendering issues
    # Icons are displayed via img tags in the content instead

    # Use YAML library to properly escape special characters
    frontmatter = "---\n"
    frontmatter += yaml.dump(frontmatter_data, default_flow_style=False, allow_unicode=True)
    frontmatter += "---\n\n"

    # Build page content
    content = frontmatter

    # Don't add icon images - they cause Mintlify rendering issues
    # Just add the readme content directly

    # Remove duplicate H1 title if present at the start of readme
    # (Mintlify uses frontmatter title as H1, so we don't want duplicates)
    readme_lines = readme.strip().split('\n')
    if readme_lines and readme_lines[0].startswith('# '):
        # Remove the first line (H1 title)
        readme = '\n'.join(readme_lines[1:]).strip()

    # Add readme content
    content += readme

    # Add metadata section if config_schema exists
    if plugin.get('config_schema'):
        content += "\n\n---\n\n## Configuration Schema\n\n"
        content += "```json\n"
        content += json.dumps(plugin['config_schema'], indent=2)
        content += "\n```\n"

    # Add support information
    support_sections = []
    if plugin.get('support_request'):
        support_sections.append(("Request Phase", "Supports processing during the REQUEST phase"))
    if plugin.get('support_response'):
        support_sections.append(("Response Phase", "Supports processing during the RESPONSE phase"))
    if plugin.get('support_log'):
        support_sections.append(("Log Phase", "Supports processing during the LOG phase"))

    if support_sections:
        content += "\n\n---\n\n## Supported Phases\n\n"
        for title, desc in support_sections:
            content += f"- **{title}**: {desc}\n"

    # Write to file
    filepath.write_text(content, encoding='utf-8')
    print(f"  ✓ Generated {filename}")

    return plugin_slug


def generate_overview_page(plugins: List[Dict[str, Any]], output_dir: Path, plugin_slugs: List[str]):
    """Generate the main overview page with a table of all plugins."""
    filepath = output_dir / "index.mdx"

    content = """---
title: 'Public Plugins'
description: 'Pre-built plugins for common use cases'
---

Datawizz provides a collection of pre-built plugins that you can use in your endpoints without writing any custom code. These public plugins cover common use cases like content filtering, PII detection, compliance checks, and more.

## Available Plugins

Browse our collection of public plugins below. Click on any plugin to view detailed documentation and configuration options.

"""

    # Build the plugins table (without icon column to avoid rendering issues)
    content += "| Plugin | Description | Phases |\n"
    content += "|--------|-------------|--------|\n"

    for plugin, slug in zip(plugins, plugin_slugs):
        name = plugin.get('name', 'Unnamed Plugin')
        description = plugin.get('description', '')

        # Build phases badge
        phases = []
        if plugin.get('support_request'):
            phases.append('REQUEST')
        if plugin.get('support_response'):
            phases.append('RESPONSE')
        if plugin.get('support_log'):
            phases.append('LOG')

        phases_str = ', '.join(phases) if phases else '-'

        # Escape pipe characters in description
        description_escaped = description.replace('|', '\\|')

        content += f"| [{name}](./{slug}) | {description_escaped} | {phases_str} |\n"

    content += "\n---\n\n"
    content += """## Using Public Plugins

To use a public plugin in your endpoint:

1. Navigate to your endpoint configuration in the Datawizz dashboard
2. Select the "Plugins" tab
3. Click "Add Plugin"
4. Choose "Public Plugins" from the plugin source dropdown
5. Select the plugin you want to use
6. Configure the plugin settings (phase, priority, async execution, etc.)
7. Save your endpoint configuration

For more information on plugin configuration and execution, see the [Plugins documentation](/plugins/plugins).

## Need a Custom Plugin?

If you need functionality that isn't covered by our public plugins, you can build your own custom plugin. See [Building Custom Plugins](/plugins/build-custom-plugins) for details.
"""

    filepath.write_text(content, encoding='utf-8')
    print(f"  ✓ Generated index.mdx (overview page)")


def update_docs_json(plugins: List[Dict[str, Any]], plugin_slugs: List[str]):
    """Update docs.json to include the new Public Plugins tab."""
    # docs.json is in the parent directory (docs root), not in __scripts
    docs_json_path = Path(__file__).parent.parent / "docs.json"

    with open(docs_json_path, 'r', encoding='utf-8') as f:
        docs_config = json.load(f)

    # Build the pages array for public plugins
    plugin_pages = ["public-plugins/index"]
    for slug in plugin_slugs:
        plugin_pages.append(f"public-plugins/{slug}")

    # Create the new tab structure
    public_plugins_tab = {
        "tab": "Public Plugins",
        "groups": [
            {
                "group": "Plugins",
                "pages": plugin_pages
            }
        ]
    }

    # Check if Public Plugins tab already exists
    existing_tabs = docs_config['navigation']['tabs']
    public_plugins_exists = any(tab.get('tab') == 'Public Plugins' for tab in existing_tabs)

    if public_plugins_exists:
        # Update existing tab
        for i, tab in enumerate(existing_tabs):
            if tab.get('tab') == 'Public Plugins':
                existing_tabs[i] = public_plugins_tab
                print("  ✓ Updated existing Public Plugins tab in docs.json")
                break
    else:
        # Add new tab
        existing_tabs.append(public_plugins_tab)
        print("  ✓ Added new Public Plugins tab to docs.json")

    # Write back to docs.json
    with open(docs_json_path, 'w', encoding='utf-8') as f:
        json.dump(docs_config, f, indent=2)
        f.write('\n')  # Add trailing newline


def main():
    """Main execution function."""
    print("Generating public plugin documentation...\n")

    # Initialize Supabase client
    print("1. Connecting to Supabase...")
    client = get_supabase_client()
    print("   ✓ Connected\n")

    # Fetch plugins
    print("2. Fetching plugins from public_plugin view...")
    plugins = fetch_public_plugins(client)
    print(f"   ✓ Found {len(plugins)} plugins\n")

    if not plugins:
        print("No plugins found. Exiting.")
        return

    # Create output directory in docs root (parent of __scripts)
    output_dir = Path(__file__).parent.parent / "public-plugins"
    output_dir.mkdir(exist_ok=True)
    print(f"3. Generating plugin pages in {output_dir}...")

    # Generate individual plugin pages
    plugin_slugs = []
    for plugin in plugins:
        slug = generate_plugin_page(plugin, output_dir)
        plugin_slugs.append(slug)

    print()

    # Generate overview page
    print("4. Generating overview page...")
    generate_overview_page(plugins, output_dir, plugin_slugs)
    print()

    # Update docs.json
    print("5. Updating docs.json configuration...")
    update_docs_json(plugins, plugin_slugs)
    print()

    print(f"✅ Successfully generated documentation for {len(plugins)} plugins!")
    print(f"\nPages created in: {output_dir}")
    print("\nNext steps:")
    print("1. Review the generated pages")
    print("2. Commit the changes to your repository")
    print("3. Deploy your documentation")


if __name__ == "__main__":
    main()
