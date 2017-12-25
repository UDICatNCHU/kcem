from distutils.core import setup

setup(
    name = 'kcem',
    packages = ['kcem'],
    package_data={'kcem':['utils/*', 'wiki/*', 'wiki/crawler/*', 'management/commands/*']},
    version = '3.8',
    description = 'kcem class file',
    author = 'davidtnfsh',
    author_email = 'davidtnfsh@gmail.com',
    url = 'https://github.com/udicatnchu/kcem',
    download_url = 'https://github.com/udicatnchu/kcem/archive/v3.8.tar.gz',
    keywords = ['kcem'],
    classifiers = [],
    license='GPL3.0',
    install_requires=[
        'simplejson',
        'requests',
        'pymongo',
        'bs4',
        'lxml',
        'jieba',
        'numpy',
        'ngram',
        'pytest',
        'json-lines',
        'pyquery',
    ],
    dependency_links=[
        'git+git://github.com/yichen0831/opencc-python.git@master#egg=opencc-python',
        'git+git://github.com/attardi/wikiextractor.git@2a5e6aebc030c936c7afd0c349e6826c4d02b871',
    ],
    zip_safe=True
)
