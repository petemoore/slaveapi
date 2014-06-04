from setuptools import setup

from slaveapi import __version__

setup(
    name="slaveapi",
    version=__version__,
    description="A tool for interacting with build and test slaves.",
    author="Mozilla Release Engineering",
    packages=["slaveapi", "slaveapi.actions", "slaveapi.clients", "slaveapi.web", "slaveapi.machines", "slaveapi.util"],
    scripts=["slaveapi-server.py"],
    install_requires=[
        "gevent==0.13.8",
        "greenlet==0.4.1",
        "pycrypto>=2.6",
        "Jinja2>=2.7.1",
        "MarkupSafe>=0.18",
        "WebOb>=1.2.3",
        "requests>=1.2.3",
        "bzrest==0.7",
        "dnspython>=1.11.0",
        "paramiko>=1.11.0",
        "flask==0.10.1",
        "werkzeug==0.9.3",
        "itsdangerous==0.23",
        "docopt>=0.6.1",
        "python-daemon>=1.5.5",
        "gevent_subprocess==0.1.1",
        "furl>=0.3.5",
        "orderedmultidict>=0.7.1",
        "pytz>=2013.7",
        "python-dateutil>=1.5",
        "mozpoolclient==0.1.5",
    ],
)
