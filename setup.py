#!/usr/bin/env python3
from setuptools import setup, find_packages
import os

# Make sure scripts are executable
bin_dir = os.path.join(os.path.dirname(__file__), 'bin')
for script in os.listdir(bin_dir):
    script_path = os.path.join(bin_dir, script)
    if not script_path.endswith('.py') and os.path.isfile(script_path):
        os.chmod(script_path, 0o755)

setup(
    name="leetcode-tools",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.0",
        "rich>=10.0.0",
        "mysql-connector-python>=8.0.0",
        "appdirs>=1.4.4",
    ],
    scripts=[
        'bin/leetcode-cli',
        'bin/leetcode-selector',
    ],
    entry_points={
        'console_scripts': [
            'leetcode-cli=leetcode_tools.cli.main:main',
            'leetcode-selector=leetcode_tools.cli.main:selector_main',
        ],
    },
    package_data={
        'leetcode_tools': ['data/*.json'],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="LeetCode CLI and Problem Selector Tools",
    keywords="leetcode, cli, problem selector",
    python_requires=">=3.6",
)