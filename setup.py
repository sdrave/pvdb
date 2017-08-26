from setuptools import setup

setup(
    name='pvdb',
    version='0.1',
    description="Python visual debugger inspired by Philip Guo's Python Tutor",
    url='https://github.com/sdrave/pvdb',
    author='Stephan Rave',
    autor_email='pvdb@stephanrave.de',
    license='GPL-3.0+',
    py_modules=['pvdb'],
    entry_points={'console_scripts': ['pvdb=pvdb:main']},
    zip_save=True
)
