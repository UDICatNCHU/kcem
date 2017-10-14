from distutils.core import setup

setup(
    name = 'kcem',
    packages = ['kcem'],
    package_data={'kcem':['utils/*']},
    version = '2.3',
    description = 'kcem class file',
    author = 'davidtnfsh',
    author_email = 'davidtnfsh@gmail.com',
    url = 'https://github.com/udicatnchu/kcem',
    download_url = 'https://github.com/udicatnchu/kcem/archive/v2.3.tar.gz',
    keywords = ['kcem'],
    classifiers = [],
    license='GPL3.0',
    install_requires=[
        'pymongo',
        'simplejson',
        'requests',
        'jieba',
    ],
    zip_safe=True
)
