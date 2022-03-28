from setuptools import setup, find_packages

setup(
    name="ig-mbs-scheduler",
    version="0.1.0",
    description="",
    long_description="",
    url="",
    author="",
    author_email="",
    license="",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "Click",
    ],
    entry_points={
        "console_scripts": [
            "ig-mbs-scheduler=ig_mbs_scheduler.ig_mbs_scheduler:cli",
        ],
    },
)
