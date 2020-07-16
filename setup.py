
import setuptools
import re

with open("README.md", "r") as fh:
    long_description = fh.read()

version = ''
with open('debug_cog/__init__.py') as f:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE).group(1)

setuptools.setup(
    name="debug-cog",
    version=version,
    author="Ilovetocode",
    description="A discord.py debug cog",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ilovetocode2019/Debug-Cog",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)