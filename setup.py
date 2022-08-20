import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="streams",
    version="1.0.0",
    author="ramsteak",
    author_email="ramsteak.git@gmail.com",
    url="https://github.com/ramsteak/streams",
    description="A package to easily handle streams of data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GPLv3 License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
