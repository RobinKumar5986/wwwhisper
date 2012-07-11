from distutils.core import setup

setup(
    name = 'wwwhisper',
    description = 'Access control for HTTP resources using Persona '\
        '(aka BrowserID).',
    version = '0.1',
    package_dir = { '': 'django_wwwhisper'},
    packages = [
        'wwwhisper_admin',
        'wwwhisper_auth',
        'wwwhisper_service',
        ],
    author = 'Jan Wrobel',
    author_email = 'wrr@mixedbit.org',
    url = 'https://github.com/wrr/wwwhisper',
    classifiers  =  [
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)'
        'Operating System :: OS Independent',
        'Programming Language :: JavaScript',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Site Management',
        ],

#    install_requires = '',
#    package_data = {'wwwhisper': ['auth_static']},
)
