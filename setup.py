from distutils.core import setup

setup(
    name = 'kcem',
    packages = ['kcem'],
    package_data={'kcem':['utils/*']},
    version = '3.0',
    description = 'kcem class file',
    author = 'davidtnfsh',
    author_email = 'davidtnfsh@gmail.com',
    url = 'https://github.com/udicatnchu/kcem',
    download_url = 'https://github.com/udicatnchu/kcem/archive/v3.0.tar.gz',
    keywords = ['kcem'],
    classifiers = [],
    license='GPL3.0',
    install_requires=[
        'pymongo',
        'simplejson',
        'requests',
        'kcmApp',
    ],
    zip_safe=True
)
