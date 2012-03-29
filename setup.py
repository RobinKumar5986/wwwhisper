from setuptools import setup, find_packages

setup(
    name = 'wwwhisper',
    version = '1.0',
    url = 'https://github.com/wrr/wwwhisper/',
    license = 'GPL',
    description = 'Access control for HTTP resources using BrowserID',
    author = 'Jan Wrobel',
    packages = find_packages('src'),
    package_dir = {'': 'src'},
    install_requires = ['setuptools'],
)
