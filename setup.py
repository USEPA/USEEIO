from distutils.core import setup

setup(
    name='useeiopy',
    version='0.1',
    packages=['useeiopy'],
    package_data={'useeiopy': ["Model Builds/*.*"]},
    install_requires=['IO-Model-Builder>=1.1','pandas>=0.17'],
    url='http://www.github.com/usepa/useeio',
    license='CC0',
    author='Wesley Ingwersen',
    author_email='ingwersen.wesley@epa.gov',
    description='Python 3.x package for assembling and calculating environmentally-extended input-output models from USEEIO Modeling Framework model components.'
)
