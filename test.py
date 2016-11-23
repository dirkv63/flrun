import coverage
import unittest
import os

cov = coverage.coverage(branch=True, include='competition/*')
cov.start()

suite = unittest.TestLoader().discover('tests')
unittest.TextTestRunner(verbosity=2).run(suite)

cov.stop()
cov.report()
basedir = "c:\\temp\\coverage"
covdir = os.path.join(basedir, 'FlaskRun')
cov.html_report(directory=covdir)
print('HTML version: file://%s\\index.html' % covdir)
