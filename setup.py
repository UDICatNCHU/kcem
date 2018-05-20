from distutils.core import setup

setup(
    name = 'kcem',
    packages = ['kcem'],
    package_data={'kcem':['crawler/*', 'management/commands/*', 'utils/*', 'migrations/*']},
    version = '6.3',
    description = 'kcem class file',
    author = 'davidtnfsh',
    author_email = 'davidtnfsh@gmail.com',
    url = 'https://github.com/udicatnchu/kcem',
    download_url = 'https://github.com/udicatnchu/kcem/archive/v6.3.tar.gz',
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
        'scipy',
        'ngram',
        'pytest',
        'json-lines',
        'pyquery',
        'kem',
        'psutil'
    ],
    dependency_links=[
        'git+git://github.com/yichen0831/opencc-python.git@master#egg=opencc-python',
        'git+git://github.com/attardi/wikiextractor.git@2a5e6aebc030c936c7afd0c349e6826c4d02b871',
    ],
    zip_safe=True,
    scripts=['kcem/download_wikisql.sh']
)
