import setuptools
from tetris import VERSION

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='consoletetris',
    version=VERSION,
    packages=['tetris'],
    url='https://github.com/RedXBeard/consoletetris',
    license='MIT',
    include_package_data=True,
    author='Barbaros Yildirim',
    author_email='barbaros@boomset.com',
    description='Tetris game on console/terminal/shell',
    long_description=long_description,
    long_description_content_type="text/markdown",
    entry_points={
            'console_scripts': [
                'consoletetris = tetris.tetris:main',
            ],
        },
    classifiers=[
        'Environment :: Console',
        'Programming Language :: Python :: 3',
        'Operating System :: Unix',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
    ],
    install_requires=[
        'click',
    ]
)
