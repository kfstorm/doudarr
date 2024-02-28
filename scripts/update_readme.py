import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from config import app_config  # noqa: E402


def generate_doc():
    lines = []
    lines.append("| 环境变量 | 默认值 | 说明 |")
    lines.append("| --- | --- | --- |")
    for name, info in app_config.model_json_schema()["properties"].items():
        env_var = f"DOUDARR_{name.upper()}"
        default = info["default"]
        if default is None:
            default = "无"
        else:
            default = f"`{default}`"
        description = info["description"]
        lines.append(f"| `{env_var}` | {default} | {description} |")
    return "\n".join(lines)


def generate_readme(old_readme: str):
    doc = generate_doc()
    start_mark = "<!-- DOUDARR_SERVICE_PARAMETERS_START -->"
    end_mark = "<!-- DOUDARR_SERVICE_PARAMETERS_END -->"
    start = old_readme.index(start_mark) + len(start_mark)
    end = old_readme.index(end_mark)
    return old_readme[:start] + "\n\n" + doc + "\n\n" + old_readme[end:]


if __name__ == "__main__":
    check = len(sys.argv) > 1 and sys.argv[1] == "--check"
    readme_path = os.path.join(os.path.dirname(__file__), "..", "README.md")
    with open(readme_path, "r") as f:
        old_readme = f.read()
    new_readme = generate_readme(old_readme)
    if old_readme == new_readme:
        print("README is up to date.")
    else:
        if check:
            print("README is not up to date.")
            # call git diff
            subprocess.run(
                ["git", "--no-pager", "diff", "--no-ext-diff", "--", readme_path],
                check=True,
            )
            sys.exit(1)
        else:
            with open(readme_path, "w") as f:
                f.write(new_readme)
            print("README updated.")
