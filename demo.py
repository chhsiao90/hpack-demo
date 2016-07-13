import binascii
import sys
from hpack import Encoder, Decoder
import json


def header_dict_to_tuple(header):
    assert len(header) == 1
    item = header.items()[0]
    return (item[0], item[1])


def translate_match(match):
    if not match:
        return "(not match)"

    index, name, value = match
    if not value:
        return "(patial match with index: {0})".format(index)
    return "(perfect match with index: {0})".format(index)


class Demo(object):
    def __init__(self):
        self.encoder = Encoder()
        self.decoder = Decoder()

    def run(self, headers):
        origin_len = 0
        encoded_len = 0
        for header in headers:
            header_tuple = header_dict_to_tuple(header)
            encoded = self.encoder.encode([header_tuple])

            encoded_len += len(encoded)
            origin_len += len(header_tuple[0]) + len(header_tuple[1])
            match = self.decoder.header_table.search(header_tuple[0], header_tuple[1])
            print "{0}=>{1} {2}".format(header, binascii.hexlify(encoded), translate_match(match))

            self.decoder.decode(encoded)
        print "Decompressed from {0} to {1}".format(origin_len, encoded_len)

    def pretty_print_table(self, table):
        for (k, v) in table.dynamic_entries:
            print "{0}=>{1}".format(k, v)

    def tables(self):
        print "[encoder]"
        self.pretty_print_table(self.encoder.header_table)
        print "[decoder]"
        self.pretty_print_table(self.decoder.header_table)


class StoryRunner(object):
    def __init__(self, story):
        self.story = story
        self.demo = Demo()

    def run(self):
        for i, case in enumerate(self.story["cases"]):
            self.user_input(i)
            self.demo.run(case["headers"])
        self.user_input(len(self.story["cases"]))
        print "All the cases from the story is run"

    def user_input(self, index):
        _msg = "Case({0}/{1}) (n:next t:tables) :".format(index, len(self.story["cases"]))
        c = None
        while c != "n":
            c = raw_input(_msg)
            if c == "t":
                self.demo.tables()


def main():
    with open(sys.argv[1], "r") as f:
        story = json.load(f)
    StoryRunner(story).run()


if __name__ == "__main__":
    main()
