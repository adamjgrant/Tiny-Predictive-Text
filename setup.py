from setuptools import setup, find_packages

setup(
    name='Tiny Predictive Text',
    version='12.0',
    packages=find_packages(),
    install_requires=[
        'tqdm',
        'msgpack',
        'asyncio; python_version<"3.7"',  # asyncio is part of the standard library from Python 3.7 onwards
        'datasets',
    ],
    # Include additional metadata about your project
    author='Adam Grant',
    author_email='hello@adamgrant.me',
    description='Tiny Predictive Text',
    # More metadata
)

