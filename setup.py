from setuptools import setup, find_packages

setup(
    name="sanskrit-mesh",
    version="0.1.0",
    author="Krishanu Manna",
    author_email="krishanumanna48@gmail.com",
    description="An AI-native bytecode compiler that reduces multi-agent LLM token costs by 60%+ using Paninian-inspired Intermediate Representation.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/sanskrit-mesh",
    packages=find_packages(),
    py_modules=["compiler"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires='>=3.7',
    keywords="ai, llm, agents, tokens, compression, autogen, crewai, langchain",
)
