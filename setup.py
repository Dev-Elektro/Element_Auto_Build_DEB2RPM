from setuptools import setup

setup(
    name='Element_Auto_Build_DEB2RPM',
    version='0.0.1',
    packages=['Element_Auto_Build_DEB2RPM'],
    url='https://github.com/Dev-Elektro/Element-Auto-Build-DEB2RPM',
    license='',
    author='Dev-Elektro',
    author_email='dev.elektro.sergei@gmail.com',
    description='Автоматическая сборка Element из deb в rpm пакет.',

    install_requires=[
        'bs4>=0.0.1',
        'lxml>=4.9.2',
        'requests>=2.28.2',
        'tqdm>=4.64.1',
    ],

    entry_points={
        'console_scripts':
            ['element-auto-build-deb2rpm = Element_Auto_Build_DEB2RPM.main:main']
    },
    python_requires=">=3.8",
)
