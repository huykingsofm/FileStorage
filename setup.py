import setuptools


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="file_storage",
    version="0.0.1",
    author="huykingsofm",
    author_email="huykingsofm@gmail.com",
    description="A python module for storing and searching file.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/huykingsofm/file_storage",
    project_urls={
        "Bug Tracker": "https://github.com/huykingsofm/file_storage/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3",
    install_requires=[],
    setup_requires=["pytest-runner==4.4"],
    tests_require=["pytest==4.4.1", "hks_pylib==0.0.4", "file_encryptor==0.0.1"],
    test_suite="tests",
)
