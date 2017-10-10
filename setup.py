from distutils.core import setup

setup(
    name = 'kcem',
    packages = ['kcem'],
    version = '1.7',
    description = 'kcem class file',
    author = 'davidtnfsh',
    author_email = 'davidtnfsh@gmail.com',
    url = 'https://github.com/udicatnchu/kcem',
    download_url = 'https://github.com/udicatnchu/kcem/archive/v1.7.tar.gz',
    keywords = ['kcem'],
    classifiers = [],
    license='GPL3.0',
    install_requires=[
        'pymongo',
        'simplejson',
        'requests',
        'keras',
        'click',
        'jieba',
        'tensorflow',
        'h5py'
    ],
    zip_safe=True
)
