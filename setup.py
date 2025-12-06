from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="mpolicy",
    version="0.1.0",
    author="您的姓名",
    author_email="您的邮箱",
    description="股票数据处理和技术分析工具",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/您的用户名/MPolicy",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "akshare>=1.0.0",
        "pandas>=1.0.0",
    ],
)