#!/usr/bin/env python3
"""
Setup script for QuailTrail - Workflow orchestration engine
"""

from setuptools import setup, find_packages
import os
import sys

# Read version from __init__.py
def get_version():
    version_file = os.path.join(os.path.dirname(__file__), 'quail', '__init__.py')
    if os.path.exists(version_file):
        with open(version_file, 'r') as f:
            for line in f:
                if line.startswith('__version__'):
                    return line.split('=')[1].strip().strip('"\'')
    return "0.1.0"

# Read README
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "QuailTrail: Workflow orchestration engine with dependency resolution"

# Core dependencies (minimal for core functionality)
CORE_REQUIREMENTS = [
    "PyYAML>=6.0",
    "click>=8.0",
]

# Optional dependencies
EXTRAS_REQUIRE = {
    # Database support
    'database': [
        'SQLAlchemy>=1.4,<3.0',
        'psycopg2-binary>=2.9',
        'sqlalchemy-redshift>=0.8',
    ],
    
    # MongoDB support
    'mongodb': [
        'pymongo>=4.0',
        'mongoengine>=0.28.0',
    ],
    
    # Analytics and data processing
    'analytics': [
        'pandas>=1.5',
        'numpy>=1.20',
        'scipy>=1.9',
    ],
    
    # Development dependencies
    'dev': [
        'pytest>=7.0',
        'pytest-cov>=4.0',
        'black>=22.0',
        'flake8>=5.0',
        'mypy>=1.0',
    ],
    
    # Documentation
    'docs': [
        'sphinx>=4.0',
        'sphinx-rtd-theme>=1.0',
    ],
}

# All optional dependencies
EXTRAS_REQUIRE['all'] = [
    dep for deps_list in EXTRAS_REQUIRE.values() 
    for dep in deps_list if deps_list != EXTRAS_REQUIRE.get('dev', [])
]

setup(
    name="quailtrail",
    version=get_version(),
    description="QuailTrail: Workflow orchestration engine with dependency resolution",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    
    # Author information
    author="QuailTrail Team",
    author_email="dev@quailtrail.com",
    
    # URLs
    url="https://github.com/lbundalian/quail",
    project_urls={
        "Bug Reports": "https://github.com/lbundalian/quail/issues",
        "Source": "https://github.com/lbundalian/quail",
        "Documentation": "https://github.com/lbundalian/quail/wiki",
    },
    
    # Package discovery
    packages=find_packages(exclude=['tests*', 'prototype*', 'pricing_quality_pipeline*']),
    
    # Python version requirement
    python_requires=">=3.10",
    
    # Dependencies
    install_requires=CORE_REQUIREMENTS,
    extras_require=EXTRAS_REQUIRE,
    
    # Entry points
    entry_points={
        'console_scripts': [
            'quail=quail.cli:main',
            'quailtrail=quail.cli:main',
        ],
    },
    
    # Package data
    include_package_data=True,
    package_data={
        'quail': ['*.yml', '*.yaml', '*.json'],
    },
    
    # Classifiers
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Data Engineers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Distributed Computing",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Database :: Database Engines/Servers",
    ],
    
    # Keywords
    keywords="workflow orchestration pipeline data-quality dependency-resolution",
    
    # License
    license="MIT",
    
    # Zip safe
    zip_safe=False,
)