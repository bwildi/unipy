import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="unityrde",
    version="0.0.4",
    author="Billy Wildi",
    author_email="bwildi94@gmail.com",
    description="A Python package for the Unity Analytics Raw Data Export REST API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/bwildi/unityrde/tree/master/unityrde",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.5',
)