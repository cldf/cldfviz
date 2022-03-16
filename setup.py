from setuptools import setup, find_packages


setup(
    name='cldfviz',
    version='0.7.0',
    author='Robert Forkel',
    author_email='dlce.rdm@eva.mpg.de',
    description='A cldfbench plugin to create vizualisations of CLDF datasets',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    keywords='',
    license='Apache 2.0',
    url='https://github.com/cldf/cldfviz',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'cldfbench.commands': [
            'cldfviz=cldfviz.commands',
        ],
    },
    platforms='any',
    python_requires='>=3.6',
    install_requires=[
        'clldutils>=3.11.1',
        'pycldf>=1.25.1',
        'cldfbench>=1.5.0',
        'attrs',
        'termcolor',
        'jinja2',
        'pyglottolog',
        'tqdm',
        'yattag',
        'matplotlib',
        'numpy',
    ],
    extras_require={
        'cartopy': [
            # Newer cartopy requires PROJ >= 8 which isn't available by default
            # on current Ubuntu.
            'cartopy<0.20',
            'scipy',
        ],
        'dev': ['flake8', 'wheel', 'twine'],
        'test': [
            'pytest>=5',
            'pytest-mock',
            'pytest-cov',
            'coverage>=4.2',
        ],
    },
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy'
    ],
)
