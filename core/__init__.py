__version__ = '1.0.0'

import os

BaseDir = os.path.dirname(os.path.abspath(__file__))
TemplatesDir = os.path.join(BaseDir, 'templates')

DefaultConfig = "./config/config.ini"
ReaderSection = "reader"
LoggerSection = "logger"
