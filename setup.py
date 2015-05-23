from setuptools import setup

setup(
    name='solarmax',
    description='Script to read statistics from Solarmax inverter and output in graphite compatible format.',

    author='Johan Bloemberg',
    author_email='mail@ijohan.nl',
    url='https://github.com/aequitas/solarmax',

    py_modules=['solarmax'],
    entry_points={
        'console_scripts': [
            "solarmax = solarmax:main",
        ]
    },
)
