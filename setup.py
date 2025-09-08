#!/usr/bin/env python3
"""
shepherd.py - Smart URL router for browser profiles
"""

from setuptools import setup, find_packages
import os

# Read version from __version__.py
exec(open("__version__.py").read())

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="shepherd-browser-router",
    version=__version__,
    author="shepherd.py contributors",
    description="A smart URL router that guides web links to the right browser profile",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/d1rewolf/shepherd",
    py_modules=["shepherd"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: X11 Applications",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Internet :: WWW/HTTP :: Browsers",
        "Topic :: Utilities",
    ],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "shepherd.py=shepherd:main",
        ],
    },
    install_requires=[],  # No external dependencies!
    extras_require={
        "dev": [
            "pytest>=6.0",
            "black",
            "flake8",
        ],
    },
    keywords="browser, url, router, profile, chromium, chrome",
    project_urls={
        "Bug Tracker": "https://github.com/d1rewolf/shepherd/issues",
        "Source": "https://github.com/d1rewolf/shepherd",
    },
)