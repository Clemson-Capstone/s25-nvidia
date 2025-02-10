import yaml

# Load environment.yaml
with open("environment.yaml", "r") as file:
    env_data = yaml.safe_load(file)

# Extract dependencies
dependencies = env_data.get("dependencies", [])
requirements = []

for dep in dependencies:
    if isinstance(dep, str):
        # Conda-style dependency (e.g., "numpy=1.21.2")
        print(dep)
        if "=" in dep:
            package, version, source = dep.split("=")
            requirements.append(f"{package}=={version}")
        else:
            requirements.append(dep)
    elif isinstance(dep, dict) and "pip" in dep:
        # pip-style dependencies
        requirements.extend(dep["pip"])

# Write to requirements.txt
with open("requirements.txt", "w") as file:
    file.write("\n".join(requirements))

print("requirements.txt generated successfully.")

