from HTMLParser import HTMLParser

__author__ = 'warenix'


class BaseParser(HTMLParser):
    def checkInTag(self, target_tag, target_attr_name, target_attr_value, tag, attrs):
        if target_tag == tag:
            for attr in attrs:
                if target_attr_name == attr[0] and target_attr_value == attr[1]:
                    return True
        return False

    def hasAttr(self, target_attr_name, attrs):
        for attr in attrs:
            if target_attr_name == attr[0]:
                return True
        return False

    def getFromAttrs(self, target_attr_name, attrs):
        for attr in attrs:
            if target_attr_name == attr[0]:
                return attr[1]
        return None
