import sys

import os

sys.path.insert(1, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

import getopt
from renthse.provider.centanet import ParserCentanet
from renthse.provider.p591 import Parser591
from renthse.provider.hse28 import ParserHse28

__author__ = 'warenix'


def main(argv):
    provider = None

    try:
        opts, args = getopt.getopt(argv, "hp:", ["provider="])
    except getopt.GetoptError:
        print 'provider.py -p <provider>'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'provider.py -p <provider>'
            sys.exit()
        elif opt in ("-p", "--provider"):
            provider = arg

    if provider is not None:
        print 'provider is', provider

        if provider == '591':
            parser = Parser591()
            for i in range(1, 100):
                parser.fetch_page(i)
        elif provider == 'centanet':
            parser = ParserCentanet()
            for i in range(1, 300):
                parser.fetch_page(i)
        elif provider == 'hse28':
            parser = ParserHse28()
            parser.fetch_page()


if __name__ == '__main__':
    main(sys.argv[1:])
