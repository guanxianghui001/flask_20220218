
class Base(object):
    host = '0.0.0.0'

class Production(Base):
    DEBUG = False


class Test(Base):
    DEBUG = True
