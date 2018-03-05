from setuptools import setup
import os
from codecs import open

with open('README.rst', 'r', 'utf-8') as f:
    readme = f.read()

here = os.path.abspath(os.path.dirname(__file__))

about = {}
with open(os.path.join(here, 'gpm_player', '__version__.py'),
          'r', 'utf-8') as f:
    exec(f.read(), about)

with open('requirements.txt', 'r', 'utf-8') as f:
    install_requires = f.read().split('\n')

setup(
    name=about['__title__'],
    version=about['__version__'],
    author=about['__author__'],
    author_email=about['__author_email__'],
    description=about['__description__'],
    long_description=readme,
    packages=['gpm_player'],
    python_requires='>=3.5',
    license=about['__license__'],
    url=about['__url__'],
    py_modules=['gpm_player'],
    entry_points={
        'console_scripts': [
            'gpm-station = gpm_player.station:main',
            'gpm-playlist = gpm_player.playlist:main',
        ]
    },
    keyword=['gmusicapi', 'music', 'music-player'],
    install_requires=install_requires,
    classifiers=[
        'Environment :: Console',
        'License :: OSI Approved :: MIT License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Topic :: Multimedia :: Sound/Audio :: Players',
        'Topic :: Terminals',
    ],
)
