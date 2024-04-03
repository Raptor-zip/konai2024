from setuptools import find_packages, setup

package_name = 'konai2024_python'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='kaibuchisoma',
    maintainer_email='72306@toyota.kosen-ac.jp',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'main = konai2024_python.main:main',
            'write_read_serial = konai2024_python.write_read_serial:main',
            'webserver = konai2024_python.webserver:main',
            'odometry = konai2024_python.odometry:main'
        ],
    },
)
