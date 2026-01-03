from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from pydantic_ai import FunctionToolset, Tool


@dataclass
class SkillMetadata:
    """Metadata for a registered skill."""

    name: str
    folder_path: Path
    skill_md_path: Path
    description: str
    license: str | None = None


@dataclass
class Skills:
    """
    Manages a collection of skills that can be loaded and used as tools.

    Skills are stored as markdown files with YAML frontmatter metadata.
    Each skill folder should contain a skill.md file (or skill.md in subdirectories).
    """

    _skills: dict[str, SkillMetadata] = field(default_factory=dict)

    def register_skill(self, skill_folder: str | Path) -> None:
        """
        Register skills from a folder by searching for skill.md files.

        This method recursively searches the skill folder for all skill.md files
        and registers each one. Multiple skills can exist in subdirectories:
        - skill_folder/skill_1/skill.md
        - skill_folder/skill_2/skill.md
        - skill_folder/foo/bar/skill.md

        Args:
            skill_folder: Path to the folder containing skill definitions (str or Path).

        Raises:
            FileNotFoundError: If the skill folder doesn't exist.
            ValueError: If no skill.md files are found or metadata is invalid.
        """
        folder_path = Path(skill_folder) if isinstance(skill_folder, str) else skill_folder

        if not folder_path.exists():
            raise FileNotFoundError(f"Skill folder not found: {skill_folder}")

        if not folder_path.is_dir():
            raise ValueError(f"Skill path must be a directory: {skill_folder}")

        # Recursively search for all skill.md files
        skill_md_files = list(folder_path.rglob("skill.md"))

        if not skill_md_files:
            raise ValueError(f"No skill.md files found in folder: {skill_folder}")

        # Process all skill.md files found
        for skill_md_path in skill_md_files:
            # Extract metadata from the skill.md file
            metadata = self._extract_metadata(skill_md_path)

            # Use the skill folder that contains this skill.md
            skill_folder_path = skill_md_path.parent

            # Register the skill using the name from metadata
            self._skills[metadata["name"]] = SkillMetadata(
                name=metadata["name"],
                folder_path=skill_folder_path,
                skill_md_path=skill_md_path,
                description=metadata["description"],
                license=metadata.get("license"),
            )

    def _extract_metadata(self, skill_md_path: Path) -> dict[str, str]:
        """
        Extract metadata from the YAML frontmatter in skill.md.

        Args:
            skill_md_path: Path to the skill.md file.

        Returns:
            Dictionary containing metadata with at least 'name' and 'description'.

        Raises:
            ValueError: If frontmatter is missing or description is not provided.
        """
        try:
            content = skill_md_path.read_text(encoding="utf-8")
        except Exception as e:
            raise ValueError(f"Failed to read skill.md at {skill_md_path}: {e}") from e

        # Find YAML frontmatter between --- markers
        frontmatter_pattern = r"^---\s*\n(.*?)\n---\s*\n"
        match = re.match(frontmatter_pattern, content, re.DOTALL)

        if not match:
            raise ValueError(
                f"No YAML frontmatter found in {skill_md_path}. "
                "Expected format:\n---\nname: skill-name\ndescription: skill-description\n---"
            )

        frontmatter_text = match.group(1)

        try:
            metadata = yaml.safe_load(frontmatter_text)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML frontmatter in {skill_md_path}: {e}") from e

        # Validate required fields
        if not isinstance(metadata, dict):
            raise TypeError(f"YAML frontmatter must be a dictionary in {skill_md_path}")

        if "name" not in metadata:
            raise ValueError(f"Missing required 'name' field in {skill_md_path}")

        if not metadata["name"] or not metadata["name"].strip():
            raise ValueError(f"Empty 'name' field in {skill_md_path}")

        if "description" not in metadata:
            raise ValueError(f"Missing required 'description' field in {skill_md_path}")

        if not metadata["description"] or not metadata["description"].strip():
            raise ValueError(f"Empty 'description' field in {skill_md_path}")

        return metadata

    def skill_load(self, skill_name: str, artifact_path: str | None = None) -> str:
        """
        Load a skill's content from its folder.

        This function loads the content of a skill artifact. If no artifact path
        is provided or the path is empty, it loads the default skill.md file.

        This is an AI tool function, so it returns error messages as strings
        rather than raising exceptions.

        Args:
            skill_name: Name of the skill to load.
            artifact_path: Optional path to a specific artifact file within the skill folder.
                          If None or empty, loads skill.md.

        Returns:
            The content of the requested skill artifact, or an error message string.
        """
        if skill_name not in self._skills:
            available = ", ".join(self._skills.keys()) if self._skills else "none"
            return f"Error: Skill '{skill_name}' not registered. Available skills: {available}"

        skill_meta = self._skills[skill_name]

        # Determine which file to load
        if artifact_path is None or artifact_path.strip() == "":
            target_file = skill_meta.skill_md_path
        else:
            target_file = skill_meta.folder_path / artifact_path

        if not target_file.exists():
            return f"Error: Artifact file not found: {target_file}"

        try:
            return target_file.read_text(encoding="utf-8")
        except Exception as e:
            return f"Error: Failed to read artifact file {target_file}: {e}"

    def toolset(self) -> FunctionToolset[object]:
        """
        Create a FunctionToolset with dynamically generated skill_load tool.

        The tool description includes metadata about all registered skills,
        providing AI agents with context about available skills and instructions
        on how to use them.

        Returns:
            A FunctionToolset containing the skill_load tool with dynamic schema.
        """
        # Build detailed skills list with metadata
        if self._skills:
            skills_list = []
            for name, meta in self._skills.items():
                skill_entry = f"  - name: {name}\n    description: {meta.description}"
                if meta.license:
                    skill_entry += f"\n    license: {meta.license}"
                skills_list.append(skill_entry)
            skills_text = "\n\n".join(skills_list)
        else:
            skills_text = "  (No skills registered yet)"

        description = f"""Load skill documentation and artifacts to help answer user questions.

SKILL SYSTEM:
Skills are curated knowledge resources containing best practices, documentation,
and implementation guides. Use them to provide accurate, contextual assistance.

AVAILABLE SKILLS:
{skills_text}

USAGE INSTRUCTIONS:
1. When a user asks a question, identify if any registered skill is relevant
2. Load the appropriate skill using skill_load(skill_name="<name>")
3. Read and understand the skill content
4. If necessary and the skill.md references other files (examples, cheatsheets, etc.),
   you can use this same tool again with artifact_path to load those files
5. Use the loaded information to provide a comprehensive answer

PARAMETERS:
- skill_name: The name of the skill to load (required)
- artifact_path: Optional path to a specific file within the skill folder
  - If omitted or empty, loads the main skill.md file

EXAMPLES:
- skill_load(skill_name="python-best-practices")
  # Then if necessary and skill.md mentions "see examples.py":
- skill_load(skill_name="python-best-practices", artifact_path="examples.py")

Always load relevant skills BEFORE answering questions that fall within their domain.
If needed for a complete answer, you can load additional referenced files."""

        # Create dynamic schema for skill_load with enhanced parameter descriptions
        skill_names_list = list(self._skills.keys())
        skill_name_description = "Name of the skill to load"
        if skill_names_list:
            skill_name_description += f". Available: {', '.join(skill_names_list)}"

        skill_load_tool = Tool.from_schema(
            function=self.skill_load,
            name="skill_load",
            description=description,
            json_schema={
                "type": "object",
                "properties": {
                    "skill_name": {
                        "type": "string",
                        "description": skill_name_description,
                    },
                    "artifact_path": {
                        "type": ["string", "null"],
                        "description": "Optional path to a specific artifact file within the skill folder. If None or empty, loads skill.md. If skill.md references other files (e.g., examples.py) and you need them, you can use this same tool again with artifact_path to load them.",
                    },
                },
                "required": ["skill_name"],
                "additionalProperties": False,
            },
            takes_ctx=False,
        )

        return FunctionToolset(tools=[skill_load_tool])
