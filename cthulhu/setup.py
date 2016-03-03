from setuptools import setup

setup(
    name="calamari_cthulhu",
    version="0.1",
    packages=['cthulhu', 'cthulhu.manager', 'cthulhu.persistence'],
    url="http://www.inktank.com/enterprise/",
    author="Inktank Storage Inc.",
    author_email="info@inktank.com",
    license="LGPL-2.1+",
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'cthulhu-manager = cthulhu.manager.manager:main',
            'calamari-ctl = cthulhu.calamari_ctl:main'
        ]
    }
)
