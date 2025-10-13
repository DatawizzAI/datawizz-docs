# Public Plugins Documentation Generator

This script automatically generates documentation pages for all public plugins by fetching data from the Supabase `public_plugin` view.

## What It Does

The script performs the following tasks:

1. **Fetches plugin data** from the Supabase `public_plugin` view
2. **Generates individual MDX pages** for each plugin with:
   - Plugin name, description, and icon
   - Full README content
   - Configuration schema (if available)
   - Supported phases (REQUEST, RESPONSE, LOG)
3. **Creates an overview page** (`public-plugins/index.mdx`) with a table of all plugins
4. **Updates `docs.json`** to add the "Public Plugins" tab to the navigation

## Prerequisites

- Python 3.7 or higher
- Access to the Datawizz Supabase database
- Supabase credentials (URL and API key)

## Setup

1. Install Python dependencies:

```bash
pip install -r requirements.txt
```

2. Set up environment variables with your Supabase credentials:

```bash
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_KEY="your-anon-or-service-key"
```

Alternatively, you can create a `.env` file in the project root (make sure to add it to `.gitignore`):

```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-or-service-key
```

## Usage

Run the script from the documentation root directory:

```bash
python generate_plugin_docs.py
```

The script will:
- Connect to Supabase
- Fetch all plugins from the `public_plugin` view
- Generate MDX files in the `public-plugins/` directory
- Update `docs.json` with the new navigation structure

## Output Structure

```
public-plugins/
├── index.mdx                 # Overview page with plugins table
├── plugin-name-1.mdx         # Individual plugin page
├── plugin-name-2.mdx         # Individual plugin page
└── ...
```

## Database Schema

The script expects the following columns from the `public_plugin` view:

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Plugin unique identifier |
| `created_at` | timestamp | Creation timestamp |
| `name` | text | Plugin name |
| `description` | text | Short description |
| `config_schema` | jsonb | Configuration schema (optional) |
| `support_request` | boolean | Supports REQUEST phase |
| `support_response` | boolean | Supports RESPONSE phase |
| `support_log` | boolean | Supports LOG phase |
| `icon` | text | URL or path to plugin icon |
| `readme` | text | Full plugin documentation (Markdown) |

## View Definition

The `public_plugin` view filters plugins from the main `plugin` table:

```sql
CREATE OR REPLACE VIEW public.public_plugin AS
SELECT id, created_at, name, description, config_schema,
       support_request, support_response, support_log, icon, readme
FROM public.plugin
WHERE project IN ('79ffa61a-7d17-41b7-b2d6-98d889258d43');
```

## Updating Documentation

To refresh the plugin documentation after changes in the database:

1. Run the script again: `python generate_plugin_docs.py`
2. Review the generated/updated pages
3. Commit the changes to your repository
4. Deploy your documentation

## Notes

- The script will **overwrite existing files** in the `public-plugins/` directory
- Plugin names are converted to URL-friendly slugs (lowercase, hyphens instead of spaces)
- If a plugin has no `readme` content, a default message will be displayed
- Icons are currently referenced by URL - ensure icon URLs are publicly accessible

## Troubleshooting

**Error: "SUPABASE_URL and SUPABASE_KEY environment variables must be set"**
- Make sure you've exported the environment variables or created a `.env` file

**Error: "supabase package not found"**
- Install dependencies: `pip install -r requirements.txt`

**Error fetching plugins from Supabase**
- Verify your Supabase credentials are correct
- Ensure your API key has read access to the `public_plugin` view
- Check that the view exists in your database

**No plugins found**
- Verify that the `public_plugin` view contains data
- Check the project ID filter in the view definition matches your project
