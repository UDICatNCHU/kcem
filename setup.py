from distutils.core import setup

setup(
    name = 'kcem',
    packages = ['kcem'],
    package_data={'kcem':['utils/*']},
    version = '2.8',
    description = 'kcem class file',
    author = 'davidtnfsh',
    author_email = 'davidtnfsh@gmail.com',
    url = 'https://github.com/udicatnchu/kcem',
    download_url = 'https://github.com/udicatnchu/kcem/archive/v2.8.tar.gz',
    keywords = ['kcem'],
    classifiers = [],
    license='GPL3.0',
    install_requires=[
        'pymongo',
        'simplejson',
        'requests',
        'jieba',
        'kcmApp',
        'kem'
    ],
    zip_safe=True
)
