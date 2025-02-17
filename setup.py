from setuptools import setup, find_packages

setup(
    name="cryptoapi",
    version="0.2",
    packages=find_packages(),
    install_requires=[
        'pandas',
        'numpy',
        'psycopg2-binary',
        'pyyaml'
    ]
) 