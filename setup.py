from setuptools import setup, find_packages
with open('README.md', encoding='utf8') as fr:
    readme = fr.read()

setup(
    name='auto_contract',
    version='0.1',
    keywords='static, contract, auto',
    description='make your scalable contracts easily for your python projects.',
    long_description=readme,
    long_description_content_type='text/markdown',
    license='MIT',
    python_requires='>=3.6.0',
    url='https://github.com/Xython/auto_orm',
    author='Xython team',
    author_email='twshere@outlook.com',
    packages=find_packages(),
    entry_points={'console_scripts': [
        'contract=contract.cli:main',
    ]},
    install_requires=['wisepy', 'yapf'],
    platforms='any',
    classifiers=[
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython'
    ],
    zip_safe=False)
