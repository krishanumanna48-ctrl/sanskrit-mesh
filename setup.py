from setuptools import setup, find_packages

setup(
    name="sanskrit-mesh",
    version="1.0.0",
    author="Krishanu Manna",
    author_email="krishanumanna48@gmail.com",
    description="AI-native bytecode compiler that reduces LLM token costs 55-75% using Paninian-inspired Intermediate Representation.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/krishanumanna48-ctrl/sanskrit-mesh",
    packages=find_packages(),
    py_modules=["compiler", "middleware", "benchmark"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.7",
    install_requires=[],           # zero hard dependencies — works out of the box
    extras_require={
        "langchain": ["langchain>=0.1.0"],
        "autogen":   ["pyautogen>=0.2.0"],
        "all":       ["langchain>=0.1.0", "pyautogen>=0.2.0"],
    },
    keywords="ai llm agents tokens compression autogen crewai langchain openai cost token-reduction context-window",
    project_urls={
        "Bug Reports": "https://github.com/krishanumanna48-ctrl/sanskrit-mesh/issues",
        "Source":      "https://github.com/krishanumanna48-ctrl/sanskrit-mesh",
    },
)
