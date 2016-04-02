import coverage
import unittest

cov = coverage.coverage(branch=True, include='competition/*')
cov.start()

suite = unittest.TestLoader().discover('tests')
unittest.TextTestRunner(verbosity=2).run(suite)

cov.stop()
cov.report()
