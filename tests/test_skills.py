from pathlib import Path

import pytest

from pydantic_ai_cognitive.skills import Skills


def create_skill_with_metadata(
    folder: Path, skill_name: str, description: str, license_info: str | None = None
) -> Path:
    """Helper to create a skill folder with proper YAML frontmatter."""
    skill_folder = folder / skill_name.replace("-", "_")
    skill_folder.mkdir()

    skill_md = skill_folder / "skill.md"
    frontmatter = f"---\nname: {skill_name}\ndescription: {description}\n"
    if license_info:
        frontmatter += f"license: {license_info}\n"
    frontmatter += f"---\n\n# {skill_name.title()}\n\nBody of the skill content."

    skill_md.write_text(frontmatter)
    return skill_folder


def test_register_skill_with_yaml_frontmatter(tmp_path: Path) -> None:
    """Test successful skill registration with YAML frontmatter."""
    skills = Skills()

    skill_folder = create_skill_with_metadata(tmp_path, "python-best-practices", "Python coding best practices")

    skills.register_skill(skill_folder)

    assert "python-best-practices" in skills._skills
    assert skills._skills["python-best-practices"].name == "python-best-practices"
    assert skills._skills["python-best-practices"].description == "Python coding best practices"
    assert skills._skills["python-best-practices"].folder_path == skill_folder
    assert skills._skills["python-best-practices"].license is None


def test_register_skill_with_license(tmp_path: Path) -> None:
    """Test skill registration with license metadata."""
    skills = Skills()

    skill_folder = create_skill_with_metadata(tmp_path, "git-workflow", "Git workflow guide", license_info="MIT")

    skills.register_skill(str(skill_folder))

    assert "git-workflow" in skills._skills
    assert skills._skills["git-workflow"].license == "MIT"


def test_register_skill_recursive_search(tmp_path: Path) -> None:
    """Test that skill.md is found in subdirectories."""
    skills = Skills()

    # Create nested structure
    parent = tmp_path / "parent_folder"
    parent.mkdir()
    skill_folder = parent / "actual_skill"
    skill_folder.mkdir()

    skill_md = skill_folder / "skill.md"
    skill_md.write_text("---\nname: nested-skill\ndescription: A nested skill\n---\n\nContent")

    # Register parent folder, should find skill.md in subdirectory
    skills.register_skill(str(parent))

    assert "nested-skill" in skills._skills
    assert skills._skills["nested-skill"].folder_path == skill_folder


def test_register_skill_folder_not_found() -> None:
    """Test error when skill folder doesn't exist."""
    skills = Skills()

    with pytest.raises(FileNotFoundError, match="Skill folder not found"):
        skills.register_skill("/nonexistent/path")


def test_register_skill_not_a_directory(tmp_path: Path) -> None:
    """Test error when skill path is not a directory."""
    skills = Skills()

    # Create a file instead of a directory
    skill_file = tmp_path / "skill_file.txt"
    skill_file.write_text("Not a directory")

    with pytest.raises(ValueError, match="must be a directory"):
        skills.register_skill(skill_file)


def test_register_skill_missing_skill_md(tmp_path: Path) -> None:
    """Test error when skill.md is missing."""
    skills = Skills()

    skill_folder = tmp_path / "incomplete_skill"
    skill_folder.mkdir()

    with pytest.raises(ValueError, match=r"No skill\.md files found"):
        skills.register_skill(skill_folder)


def test_register_skill_missing_frontmatter(tmp_path: Path) -> None:
    """Test error when YAML frontmatter is missing."""
    skills = Skills()

    skill_folder = tmp_path / "no_frontmatter"
    skill_folder.mkdir()

    skill_md = skill_folder / "skill.md"
    skill_md.write_text("# Just a heading\n\nNo frontmatter here.")

    with pytest.raises(ValueError, match="No YAML frontmatter found"):
        skills.register_skill(skill_folder)


def test_register_skill_missing_name_field(tmp_path: Path) -> None:
    """Test error when 'name' field is missing from frontmatter."""
    skills = Skills()

    skill_folder = tmp_path / "no_name"
    skill_folder.mkdir()

    skill_md = skill_folder / "skill.md"
    skill_md.write_text("---\ndescription: A description\n---\n\nContent")

    with pytest.raises(ValueError, match="Missing required 'name' field"):
        skills.register_skill(skill_folder)


def test_register_skill_missing_description_field(tmp_path: Path) -> None:
    """Test error when 'description' field is missing from frontmatter."""
    skills = Skills()

    skill_folder = tmp_path / "no_desc"
    skill_folder.mkdir()

    skill_md = skill_folder / "skill.md"
    skill_md.write_text("---\nname: test-skill\n---\n\nContent")

    with pytest.raises(ValueError, match="Missing required 'description' field"):
        skills.register_skill(skill_folder)


def test_register_skill_empty_name(tmp_path: Path) -> None:
    """Test error when name is empty."""
    skills = Skills()

    skill_folder = tmp_path / "empty_name"
    skill_folder.mkdir()

    skill_md = skill_folder / "skill.md"
    skill_md.write_text("---\nname: \ndescription: A description\n---\n\nContent")

    with pytest.raises(ValueError, match="Empty 'name' field"):
        skills.register_skill(skill_folder)


def test_register_skill_empty_description(tmp_path: Path) -> None:
    """Test error when description is empty."""
    skills = Skills()

    skill_folder = tmp_path / "empty_desc"
    skill_folder.mkdir()

    skill_md = skill_folder / "skill.md"
    skill_md.write_text("---\nname: test-skill\ndescription: \n---\n\nContent")

    with pytest.raises(ValueError, match="Empty 'description' field"):
        skills.register_skill(skill_folder)


def test_skill_load_default_artifact(tmp_path: Path) -> None:
    """Test loading the default skill.md file."""
    skills = Skills()

    skill_folder = create_skill_with_metadata(tmp_path, "my-skill", "My skill description")

    skills.register_skill(str(skill_folder))

    # Load with None
    result = skills.skill_load("my-skill", None)
    assert "name: my-skill" in result
    assert "description: My skill description" in result

    # Load with empty string
    result = skills.skill_load("my-skill", "")
    assert "name: my-skill" in result


def test_skill_load_specific_artifact(tmp_path: Path) -> None:
    """Test loading a specific artifact file."""
    skills = Skills()

    skill_folder = create_skill_with_metadata(tmp_path, "data-skill", "Data processing skill")

    # Create additional artifact
    artifact_content = "Additional artifact data"
    artifact_file = skill_folder / "example.txt"
    artifact_file.write_text(artifact_content)

    skills.register_skill(skill_folder)

    result = skills.skill_load("data-skill", "example.txt")
    assert result == artifact_content


def test_skill_load_unregistered_skill() -> None:
    """Test error message when trying to load an unregistered skill."""
    skills = Skills()

    result = skills.skill_load("nonexistent-skill")
    assert "Error: Skill 'nonexistent-skill' not registered" in result
    assert "Available skills: none" in result


def test_skill_load_missing_artifact(tmp_path: Path) -> None:
    """Test error message when artifact file doesn't exist."""
    skills = Skills()

    skill_folder = create_skill_with_metadata(tmp_path, "test-skill", "Test skill")

    skills.register_skill(skill_folder)

    result = skills.skill_load("test-skill", "missing.txt")
    assert "Error: Artifact file not found" in result


def test_toolset_creation(tmp_path: Path) -> None:
    """Test that toolset is created correctly with dynamic schema."""
    skills = Skills()

    # Register two skills
    create_skill_with_metadata(tmp_path, "skill-a", "Description for skill A", license_info="MIT")
    create_skill_with_metadata(tmp_path, "skill-b", "Description for skill B")

    for skill_folder in tmp_path.iterdir():
        skills.register_skill(skill_folder)

    toolset = skills.toolset()

    # Verify toolset has one tool (skill_load)
    assert len(toolset.tools) == 1
    assert "skill_load" in toolset.tools

    # Verify description mentions available skills in multiline format
    description = toolset.tools["skill_load"].description
    assert description is not None
    assert "name: skill-a" in description
    assert "name: skill-b" in description
    assert "description: Description for skill A" in description
    assert "description: Description for skill B" in description
    assert "license: MIT" in description
    assert "USAGE INSTRUCTIONS" in description


def test_toolset_no_skills() -> None:
    """Test toolset creation when no skills are registered."""
    skills = Skills()
    toolset = skills.toolset()

    assert len(toolset.tools) == 1
    assert "skill_load" in toolset.tools
    assert toolset.tools["skill_load"].description is not None
    assert "No skills registered" in toolset.tools["skill_load"].description


def test_toolset_includes_ai_instructions(tmp_path: Path) -> None:
    """Test that toolset description includes instructions for AI."""
    skills = Skills()

    create_skill_with_metadata(tmp_path, "test-skill", "Test description")
    for skill_folder in tmp_path.iterdir():
        skills.register_skill(str(skill_folder))

    toolset = skills.toolset()
    description = toolset.tools["skill_load"].description

    # Check for key instruction elements
    assert description is not None
    assert "SKILL SYSTEM:" in description
    assert "USAGE INSTRUCTIONS:" in description
    assert "EXAMPLES:" in description
    assert "Always load relevant skills" in description


def test_multiple_skill_registration(tmp_path: Path) -> None:
    """Test registering multiple skills."""
    skills = Skills()

    for i in range(3):
        create_skill_with_metadata(tmp_path, f"skill-{i}", f"Description for skill {i}")

    for skill_folder in tmp_path.iterdir():
        skills.register_skill(str(skill_folder))

    assert len(skills._skills) == 3
    assert "skill-0" in skills._skills
    assert "skill-1" in skills._skills
    assert "skill-2" in skills._skills


def test_skill_name_from_metadata_not_folder(tmp_path: Path) -> None:
    """Test that skill name comes from metadata, not folder name."""
    skills = Skills()

    # Folder name is different from skill name in metadata
    skill_folder = tmp_path / "folder_name"
    skill_folder.mkdir()

    skill_md = skill_folder / "skill.md"
    skill_md.write_text("---\nname: actual-skill-name\ndescription: The real name\n---\n\nContent")

    skills.register_skill(str(skill_folder))

    # Should be registered under the metadata name, not folder name
    assert "actual-skill-name" in skills._skills
    assert "folder_name" not in skills._skills
    assert skills._skills["actual-skill-name"].name == "actual-skill-name"


def test_register_multiple_skills_from_one_folder(tmp_path: Path) -> None:
    """Test registering multiple skills from a single folder with subdirectories."""
    skills = Skills()

    parent_folder = tmp_path / "all_skills"
    parent_folder.mkdir()

    # Create multiple skills in subdirectories
    skill_1 = parent_folder / "skill_1"
    skill_1.mkdir()
    (skill_1 / "skill.md").write_text("---\nname: python-basics\ndescription: Python basics\n---\n\nContent 1")

    skill_2 = parent_folder / "skill_2"
    skill_2.mkdir()
    (skill_2 / "skill.md").write_text("---\nname: python-advanced\ndescription: Advanced Python\n---\n\nContent 2")

    # Nested skill
    nested = parent_folder / "foo" / "bar"
    nested.mkdir(parents=True)
    (nested / "skill.md").write_text("---\nname: git-workflow\ndescription: Git workflow guide\n---\n\nContent 3")

    # Register all skills with a single call
    skills.register_skill(parent_folder)

    # All three skills should be registered
    assert len(skills._skills) == 3
    assert "python-basics" in skills._skills
    assert "python-advanced" in skills._skills
    assert "git-workflow" in skills._skills

    # Verify folder paths are correct
    assert skills._skills["python-basics"].folder_path == skill_1
    assert skills._skills["python-advanced"].folder_path == skill_2
    assert skills._skills["git-workflow"].folder_path == nested
