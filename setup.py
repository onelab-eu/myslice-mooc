from setuptools import setup

setup(name='myops2',
      version='2.0.0',
      description='MyOps 2',
      url='',
      author='Ciro Scognamiglio',
      author_email='ciro.scognamiglio@lip6.fr',
      license='MIT',
      packages=['myops2'],
      scripts=['myops2/bin/myops2-monitor', 'myops2/bin/myops2-shell', 'myops2/bin/myops2-web'],
      #data_files=[('/etc', ['config/planetlab.cfg-dist']),
      #            ('/etc/init.d', ['init/myops2'])],
      zip_safe=False)
