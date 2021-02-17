from setuptools import setup, version

setup(
    name="ArtDecorVsConvert",
    version="1.0",
    py_modules=["artdecorvsconvert"],
    install_requires=[
        "Click",
        "Validators",
        "requests",
        "fhir.resources"
    ],
    entry_points='''
      [console_scripts]
      artdecorvsconvert=artdecorvsconvert:cli
  ''',
)
