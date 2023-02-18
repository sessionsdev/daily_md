from setuptools import setup, find_packages

setup(
      name='daily_md',
      version='0.1.0',
      packages=find_packages(),
      install_requires=[
            # List any dependencies here
      ],
      entry_points={
            'console_scripts': [
                  'daily_md=daily_md.__main__:cli',
            ],
      },
)