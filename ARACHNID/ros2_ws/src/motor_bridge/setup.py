import os
from glob import glob
from setuptools import setup

package_name = "motor_bridge"

setup(
    name=package_name,
    version="1.0.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (os.path.join("share", package_name), glob("launch.py")),
    ],
    install_requires=["setuptools", "pyserial"],
    zip_safe=True,
    maintainer="ARACHNID Team",
    maintainer_email="team@arachnid.ai",
    description="Motor bridge node for ARACHNID autonomous rover.",
    license="MIT",
    entry_points={
        "console_scripts": [
            "motor_bridge_node = motor_bridge.motor_bridge_node:main",
        ],
    },
)
