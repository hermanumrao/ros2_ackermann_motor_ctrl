from setuptools import setup

package_name = "arduino_motor"

setup(
    name=package_name,
    version="0.0.1",
    packages=[package_name],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="your_name",
    maintainer_email="your@email.com",
    description="Arduino Motor control with BTS7960 via ROS 2",
    license="MIT",
    entry_points={
        "console_scripts": [
            "motor_node = arduino_motor.motor_node:main",
        ],
    },
)
