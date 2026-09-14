import os
from glob import glob
from setuptools import setup

package_name = "localization"

setup(
    name=package_name,
    version="1.0.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (os.path.join("share", package_name), glob("launch.py")),
    ],
    install_requires=["setuptools", "numpy"],
    zip_safe=True,
    maintainer="ARACHNID Team",
    maintainer_email="team@arachnid.ai",
    description="Localization package for ARACHNID rover.",
    license="MIT",
    entry_points={
        "console_scripts": [
            "localization_node = localization.localization_node:main",
        ],
    },
)