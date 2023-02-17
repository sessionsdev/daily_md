from setuptools import setup, find_packages

setup(
      name='py_daily',
      version='0.1.0',
      packages=find_packages(),
      install_requires=[
            # List any dependencies here
      ],
      entry_points={
            'console_scripts': [
                  'py_daily=py_daily.__main__:cli',
            ],
      },
)