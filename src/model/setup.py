import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="t4t_headstamp",                     # This is the name of the package
    version="0.0.3",                        # The initial release version
    author="Robert Sim",                     # Full name of the author
    author_email="robert.sim@tech4tracing.org",
    description="Tech4Tracing Headstamp Detector",
    long_description=long_description,      # Long description read from the the readme file
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(where='src'),    # List of all python modules to be installed
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],                                      # Information to filter the project on PyPi website
    python_requires='>=3.6',                # Minimum version requirement of the package
    py_modules=["t4t_headstamp"],           # Name of the python package
    package_dir={'':'src'},     # Directory of the source code of the package
    install_requires=['Pillow','torch','torchvision','azureml-sdk','pycocotools','scipy']
)