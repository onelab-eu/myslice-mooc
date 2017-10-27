from setuptools import setup, find_packages

setup(name='myops2',
      version='2.0.0',
      description='MyOps 2',
      url='',
      author='Ciro Scognamiglio',
      author_email='ciro.scognamiglio@lip6.fr',
      license='MIT',
      packages=find_packages(),
      #packages=['myops2','myops2.lib','myops2.monitor','myops2.oml',],
      scripts=['myops2/bin/myops2-monitor', 'myops2/bin/myops2-shell', 'myops2/bin/myops2-web', 'myops2/bin/myops-mooc'],
      #data_files=[('/etc', ['config/planetlab.cfg-dist']),
      #            ('/etc/init.d', ['init/myops2'])],
      zip_safe=False)
