import subprocess
import threading

# Function to check if a package is available on PyPI
def check_package(package, available, unavailable):
    result = subprocess.run(["pip", "search", package], capture_output=True, text=True)
    if package in result.stdout:
        print(f"Available: {package}")
        available.append(package)
    else:
        print(f"Not Available: {package}")
        unavailable.append(package)

def main():
    available_packages = []
    unavailable_packages = []

    # Read dependencies from req_test.txt
    with open('req_test.txt', 'r') as file:
        dependencies = [line.strip() for line in file.readlines()]

    threads = []
    for dep in dependencies:
        thread = threading.Thread(target=check_package, args=(dep, available_packages, unavailable_packages))
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    print(f"Available packages: {available_packages}")
    print(f"Unavailable packages: {unavailable_packages}")

    # Write available packages to requirements_maybe.txt
    with open('requirements_maybe.txt', 'w') as file:
        for package in available_packages:
            file.write(package + '\n')

if __name__ == "__main__":
    main()