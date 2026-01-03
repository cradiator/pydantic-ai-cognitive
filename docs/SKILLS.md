# Skills System

The Skills system allows you to organize and dynamically load skill documentation and artifacts that can be used by AI agents. Skills use YAML frontmatter for metadata and support recursive folder search.

## Overview

Skills are stored as markdown files with YAML frontmatter metadata. Each skill contains:
- A `skill.md` file (required) with YAML frontmatter containing metadata
- Optional additional artifact files that provide supplementary information

The system automatically:
- Searches recursively for `skill.md` files
- Parses YAML frontmatter for metadata
- Registers skills using the name from metadata (not folder name)
- Provides comprehensive instructions to AI agents on how to use skills

## Quick Start

### 1. Create a Skill with YAML Frontmatter

Create a `skill.md` file with this structure:

```markdown
---
name: python-best-practices
description: Guidance on Python coding best practices and style conventions
license: MIT
---

# Python Best Practices

Your skill content goes here...

## Sections

- Best practices
- Code examples
- Common patterns
```

**Required frontmatter fields:**
- `name`: The skill identifier (used for loading)
- `description`: Brief description shown to AI agents

**Optional frontmatter fields:**
- `license`: License information (e.g., MIT, CC-BY-4.0)

### 2. Register Skills

```python
from pydantic_ai_cognitive import Skills

skills = Skills()

# Register a single skill
skills.register_skill("./my_skills/python_practices")

# Or register multiple skills from one folder with subdirectories
skills.register_skill("./all_skills")
# This will find and register ALL skill.md files:
#   ./all_skills/skill_1/skill.md
#   ./all_skills/skill_2/skill.md
#   ./all_skills/foo/bar/skill.md
```

### 3. Use with an Agent

```python
from pydantic_ai import Agent

agent = Agent(
    "openai:gpt-4",
    toolsets=[skills.toolset()],
    system_prompt="You have access to skill documentation via skill_load."
)

result = agent.run_sync("What are Python best practices?")
```

## Skill Format

### YAML Frontmatter

The frontmatter MUST be at the beginning of `skill.md`, delimited by `---`:

```markdown
---
name: skill-identifier
description: Brief description of the skill
license: MIT
---

# Skill Content

Body of the skill...
```

**Important:**
- The `name` field becomes the skill identifier (used in `skill_load`)
- The `description` appears in the tool's available skills list
- Both `name` and `description` cannot be empty or whitespace-only
- Frontmatter parsing uses standard YAML syntax

### Directory Structure

Skills can be organized in various ways:

**Option 1: Direct folder**
```
python_practices/
  skill.md
  examples.py
```

**Option 2: Nested structure**
```
skills/
  python/
    basics/
      skill.md
    advanced/
      skill.md
```

The `register_skill()` method recursively searches for ALL `skill.md` files and registers each one found.

### Additional Artifacts

Include supplementary files alongside `skill.md`:

```
my_skill/
  skill.md
  examples.py
  cheatsheet.md
  reference.json
```

Load them using the `artifact_path` parameter:

```python
examples = skills.skill_load("my-skill", "examples.py")
cheatsheet = skills.skill_load("my-skill", "cheatsheet.md")
```

## API Reference

### `Skills` Class

The main class for managing skills.

#### Methods

##### `register_skill(skill_folder: str) -> None`

Register all skills from a folder by recursively searching for `skill.md` files.

**Parameters:**
- `skill_folder`: Path to the folder to search

**Behavior:**
- Recursively searches for ALL `skill.md` files using `rglob`
- Registers EACH skill.md file found in the folder tree
- Extracts metadata from YAML frontmatter for each skill
- Registers using the `name` from metadata (not folder name)
- Supports multiple skills in subdirectories

**Raises:**
- `FileNotFoundError`: If the skill folder doesn't exist
- `ValueError`: If no skill.md files are found, frontmatter is invalid, or required fields are missing

**Example:**
```python
skills = Skills()

# Register a single skill
skills.register_skill("./skills/python_coding")

# Register multiple skills from one folder
# If ./all_skills/ contains:
#   - skill_1/skill.md
#   - skill_2/skill.md
#   - foo/bar/skill.md
# All three will be registered with one call
skills.register_skill("./all_skills")
```

##### `skill_load(skill_name: str, artifact_path: str | None = None) -> str`

Load a skill's content from its folder.

**Parameters:**
- `skill_name`: Name of the skill (from frontmatter metadata)
- `artifact_path`: Optional path to a specific artifact file. If `None` or empty, loads `skill.md`

**Returns:**
- The content of the requested artifact as a string
- If an error occurs, returns an error message string (does NOT raise exceptions)

**Error Handling:**
This is an AI tool function, so it returns error messages instead of raising exceptions:
- `"Error: Skill '<name>' not registered. Available skills: <list>"`
- `"Error: Artifact file not found: <path>"`
- `"Error: Failed to read artifact file <path>: <reason>"`

**Example:**
```python
# Load default skill.md
content = skills.skill_load("python-best-practices")

# Load specific artifact
examples = skills.skill_load("python-best-practices", "examples.py")

# Error handling
result = skills.skill_load("nonexistent")
# Returns: "Error: Skill 'nonexistent' not registered. Available skills: ..."
```

##### `toolset() -> FunctionToolset[object]`

Create a `FunctionToolset` with a dynamically generated `skill_load` tool.

The tool description includes:
- List of all registered skills with descriptions and licenses
- Comprehensive usage instructions for AI agents
- Examples of how to use the tool
- Guidance on when to load skills

**Returns:**
- A `FunctionToolset` containing the `skill_load` tool with dynamic schema

**Example:**
```python
from pydantic_ai import Agent

toolset = skills.toolset()
# The description automatically includes all registered skills

agent = Agent("openai:gpt-4", toolsets=[toolset])
```

## AI Agent Instructions

The toolset automatically provides comprehensive instructions to AI agents:

```
SKILL SYSTEM:
Skills are curated knowledge resources containing best practices, documentation,
and implementation guides. Use them to provide accurate, contextual assistance.

AVAILABLE SKILLS:
  - name: python-best-practices
    description: Guidance on Python coding best practices
    license: MIT

  - name: git-workflow
    description: A collaborative Git workflow for team projects

USAGE INSTRUCTIONS:
1. When a user asks a question, identify if any registered skill is relevant
2. Load the appropriate skill using skill_load(skill_name="<name>")
3. Read and understand the skill content
4. Use the information to provide a comprehensive answer
5. You can load additional artifacts by specifying artifact_path parameter

Always load relevant skills BEFORE answering questions that fall within their domain.
```

## Use Cases

### 1. Coding Standards and Best Practices

Store your organization's coding standards:

```markdown
---
name: python-style-guide
description: Company Python coding standards and best practices
license: Internal
---

# Python Style Guide

## Naming Conventions
- Use snake_case for functions and variables
- Use PascalCase for classes
...
```

### 2. API Documentation

Provide API documentation that agents can reference:

```markdown
---
name: rest-api-v2
description: REST API v2 documentation and examples
---

# REST API v2

## Authentication
All requests require Bearer token...

## Endpoints
...
```

### 3. Process Documentation

Document workflows and processes:

```markdown
---
name: deployment-process
description: Production deployment process and checklist
license: CC-BY-4.0
---

# Deployment Process

## Pre-deployment Checklist
1. Run all tests
2. Update changelog
...
```

### 4. Knowledge Base

Create a knowledge base of common solutions:

```markdown
---
name: troubleshooting-guide
description: Common issues and solutions for our platform
---

# Troubleshooting Guide

## Database Connection Issues
**Symptoms:** ...
**Solution:** ...
```


## Advanced Features

### Skill Name vs Folder Name

The skill name comes from the metadata, NOT the folder name:

```markdown
<!-- In folder: my_python_folder/skill.md -->
---
name: python-advanced-patterns
description: Advanced Python patterns and techniques
---
```

```python
skills.register_skill("./my_python_folder")
# Registered as "python-advanced-patterns", not "my_python_folder"
content = skills.skill_load("python-advanced-patterns")
```

### Recursive Search for Multiple Skills

The system searches recursively and registers ALL `skill.md` files found:

```
project/
  all_skills/
    python_basics/
      skill.md  ← Registered as defined in its metadata
    python_advanced/
      skill.md  ← Also registered
    nested/
      git_tools/
        skill.md  ← Also registered
```

```python
skills.register_skill("./project/all_skills")
# Finds and registers all three skills with one call
# Each skill is registered with the name from its YAML frontmatter
```

This makes it easy to organize skills in a hierarchical structure and register them all at once.

### License Metadata

Include license information for skill attribution:

```markdown
---
name: open-source-guide
description: Best practices for open source contributions
license: CC-BY-SA-4.0
---
```

The license appears in the tool description (multiline format):
```
  - name: open-source-guide
    description: Best practices for open source contributions
    license: CC-BY-SA-4.0
```

## Complete Example

See [examples/skills_example.py](../examples/skills_example.py) for a complete working example demonstrating:
- Creating skills with YAML frontmatter
- Registering multiple skills
- Loading default and custom artifacts
- Error handling
- Integration with pydantic-ai agents
