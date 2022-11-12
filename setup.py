import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="selenium-captcha-solver",
    version="0.0.4",
    author="Improvs Tech",
    author_email="improvs.tech@gmail.com",
    description="Selenium captcha solver",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/KofeinTech/selenium-captcha",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=setuptools.find_packages(),
)
