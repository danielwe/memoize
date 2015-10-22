from setuptools import setup, find_packages


def readme():
    with open('README.md') as f:
        return f.read()


setup(
    name='memoize',
    version='0.1',
    description='Python memoization decorators supporting both instance '
                'methods and ordinary functions',
    long_description=readme(),
    url='https://github.com/danielwe/memoize',
    author='Daniel Wennberg',
    author_email='daniel.wennberg@gmail.com',
    packages=find_packages(),
)
