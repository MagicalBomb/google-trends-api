from setuptools import setup

setup(
    name='google-trends-api',
    version='2.2.2',
    packages=['google_trends_api'],
    # package_dir={'': ''},
    url='',
    license='MIT',
    author='Magicalbomb',
    author_email='17826800084g@gmail.com',
    description='Async python wrapper for google trends api',
    install_requires=['httpx', 'tenacity', 'loguru']
)
