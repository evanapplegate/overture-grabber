import subprocess
import yaml

def export_conda_environment():
    command = 'conda env export > environment.yml'
    subprocess.run(command, shell=True, check=True)

def generate_requirements_txt():
    with open('environment.yml') as f:
        data = yaml.safe_load(f)  # Use safe_load instead of load

    # Find the pip section in dependencies
    pip_packages = []
    for dependency in data.get('dependencies', []):
        if isinstance(dependency, dict) and 'pip' in dependency:
            pip_packages = dependency['pip']
            break

    with open('requirements.txt', 'w') as f:
        for package in pip_packages:
            f.write(package + '\n')

if __name__ == '__main__':
    export_conda_environment()
    generate_requirements_txt()