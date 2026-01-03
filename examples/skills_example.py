"""
Example demonstrating the Skills system.

This example shows how to:
1. Create skills with YAML frontmatter metadata
2. Register skills from folders
3. Use the skills toolset with an agent to answer questions
"""

import asyncio
import tempfile
from pathlib import Path

import history_viewer  # type: ignore[import-not-found]
from pydantic_ai import Agent

from pydantic_ai_cognitive import Skills


async def main():
    # Create a temporary directory with example skills
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create example skill 1: Python Best Practices
        python_skill = tmpdir_path / "python_best_practices"
        python_skill.mkdir()
        (python_skill / "skill.md").write_text(
            """---
name: python-best-practices
description: Guidance on Python coding best practices and style conventions
license: CC-BY-4.0
---

# Python Best Practices

This skill provides guidance on Python coding best practices.

## Key Principles

1. Write readable code - Code is read more often than written
2. Follow PEP 8 - Python's official style guide
3. Use type hints - Help catch bugs and improve IDE support
4. Write tests - Ensure code correctness and prevent regressions

## Example Code

Good example with type hints and docstring:
```python
def greet(name: str) -> str:
    '''Return a personalized greeting message.

    Args:
        name: The name of the person to greet

    Returns:
        A greeting string
    '''
    return f"Hello, {name}!"
```

## Common Patterns

- Use list comprehensions for simple transformations
- Prefer f-strings for string formatting
- Use context managers (with statements) for resource management
- Follow the Zen of Python: `import this`
- Keep functions small and focused on a single task
"""
        )

        # Create example skill 2: Git Workflow
        git_skill = tmpdir_path / "git_workflow"
        git_skill.mkdir()
        (git_skill / "skill.md").write_text(
            """---
name: git-workflow
description: A collaborative Git workflow for team projects
---

# Git Workflow

This skill describes a typical Git workflow for collaborative projects.

## Workflow Steps

1. **Create a feature branch**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make changes and commit**
   ```bash
   git add .
   git commit -m "Add feature: description"
   ```

3. **Push to remote**
   ```bash
   git push origin feature/my-feature
   ```

4. **Create a pull request**
   - Go to your repository on GitHub
   - Click "New Pull Request"
   - Add description and request reviewers

5. **Merge after review**
   - Address review comments
   - Once approved, merge the PR
   - Delete the feature branch

## Best Practices

- Keep commits atomic and focused
- Write clear commit messages
- Pull from main regularly to avoid conflicts
- Review your own code before requesting review
"""
        )

        # Initialize Skills and register all skills from the parent folder
        skills = Skills()
        skills.register_skill(tmpdir_path)

        print("=== Registered Skills ===")
        for name, meta in skills._skills.items():
            license_info = f" (License: {meta.license})" if meta.license else ""
            print(f"  - {name}: {meta.description}{license_info}")
        print()

        # Create an agent with the skills toolset
        agent = Agent(
            "google-gla:gemini-flash-lite-latest",
            toolsets=[skills.toolset()],
            system_prompt="""You are a helpful coding assistant with access to skill documentation.
When asked about coding practices or workflows, use the skill_load tool to retrieve relevant information.""",
            history_processors=[history_viewer.dump_history],
        )

        # Example 1: Ask about Python best practices
        print("=== Example 1: Python Best Practices ===")
        prompt1 = "What are Python best practices for writing functions?"
        print(f"User: {prompt1}")
        result1 = await agent.run(prompt1)
        print(f"Agent: {result1.output}")
        print()

        # Example 2: Ask about Git workflow
        print("=== Example 2: Git Workflow ===")
        prompt2 = "How do I create and merge a feature branch in Git?"
        print(f"User: {prompt2}")
        result2 = await agent.run(prompt2)
        print(f"Agent: {result2.output}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
