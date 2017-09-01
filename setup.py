from setuptools import setup

setup(
    name='pvdb',
    version='0.2.1',
    description="Python visual debugger inspired by Philip Guo's Python Tutor",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Debuggers',
        'Intended Audience :: Education',
        'Intended Audience :: Developers'
    ],
    url='https://github.com/sdrave/pvdb',
    author='Stephan Rave',
    autor_email='pvdb@stephanrave.de',
    license='GPL-3.0+',
    py_modules=['pvdb'],
    entry_points={'console_scripts': ['pvdb=pvdb:main']},
    install_requires=['pillow', 'graphviz'],
    zip_save=True
)
