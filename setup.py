from setuptools import setup, find_packages

setup(
    name="vigil-cli",
    version="1.0.0",
    description="Behavioral intelligence for autonomous agent wallets",
    author="Alfaxad Eyembe",
    author_email="alfaxadeyembe@gmail.com",
    url="https://github.com/Alfaxad/Vigil",
    packages=find_packages(),
    install_requires=[
        "click>=8.1",
        "httpx>=0.28",
    ],
    entry_points={
        "console_scripts": [
            "vigil=src.cli.main:main",
        ],
    },
    python_requires=">=3.11",
)
