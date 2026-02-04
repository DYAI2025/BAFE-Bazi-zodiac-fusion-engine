from setuptools import setup, find_packages

setup(
    name="bazodiac-engine",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.100.0",
        "uvicorn>=0.22.0",
        "pydantic>=2.0.0",
        "pyswisseph>=2.10.0",
    ],
    python_requires=">=3.10",
)
