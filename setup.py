from distutils.core import setup
from tetris import VERSION

setup(
    name='consoletetris',
    version=VERSION,
    packages=['tetris'],
    url='https://github.com/RedXBeard/consoletetris',
    license='MIT',
    include_package_data=True,
    author='Barbaros Yildirim',
    author_email='barbaros@boomset.com',
    description='',
    entry_points={
            'console_scripts': [
                'consoletetris = tetris.tetris:main',
            ],
        },
    classifiers=[
        'Environment :: Console',
        'Programming Language :: Python :: 2.7',
        'Operating System :: Unix',
    ],
    install_requires=[
        'click',
    ]
)
