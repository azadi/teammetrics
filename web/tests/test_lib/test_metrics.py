from web.lib import metrics
import web.settings as settings
import ConfigParser
import unittest

class MetricsTest(unittest.TestCase):

    # Default Config value is preserved
    defaultConfigValue = metrics.CONF_FILE

    def test_correctInput(self):
        metrics.CONF_FILE = MetricsTest.defaultConfigValue
        data = metrics.get('teammetrics','list')
        self.assertIsInstance(data,list)
        self.assertTrue(len(data)>0)
        self.assertIn('teammetrics-discuss', data)

    def test_incorrectInput(self):
        metrics.CONF_FILE = MetricsTest.defaultConfigValue
        data = metrics.get('teammetrics','blah')
        self.assertEqual(len(data),0)
        data = metrics.get('blah','teammetrics')
        self.assertEqual(len(data),0)

    def test_configFileMissing(self):
        metrics.CONF_FILE = 'SomeRandomFileThatDontExist'
        data = metrics.get('teammetrics','list')
        self.assertRaises(IOError)
        self.assertIsInstance(data,list)
        self.assertEqual(len(data),0)

    def test_identify(self):
        cdata = metrics.identify('teammetrics','list')
        self.assertIsInstance(cdata,list)
        self.assertTrue(len(cdata)>0)
        self.assertIn('teammetrics-discuss', cdata)
        
        cdata = metrics.identify('teammetrics','commits')
        self.assertIsInstance(cdata,list)
        self.assertTrue(len(cdata)>0)
        self.assertIn('teammetrics', cdata)
        
        idata = metrics.identify('teammetrics','RandomMetric')
        self.assertIsInstance(idata,list)
        self.assertEqual(len(idata), 0)
        
        idata = metrics.identify('RandomName','commitlines')
        self.assertIsInstance(idata,list)
        self.assertEqual(len(idata), 0)
        
        idata = metrics.identify('RandomName','RandomMetric')
        self.assertIsInstance(idata,list)
        self.assertEqual(len(idata), 0)
