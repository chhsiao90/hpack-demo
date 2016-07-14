import binascii
import sys
from hpack import Encoder, Decoder
import json
import struct


def header_dict_to_tuple(header):
    assert len(header) == 1
    item = header.items()[0]
    if item[0] in (b"cookie", u"cookie"):
        return (item[0], item[1], True)
    else:
        return (item[0], item[1])


def translate_match(match):
    if not match:
        return "(not match)"

    index, name, value = match
    if not value:
        return "(patial match with index: {0})".format(index)
    return "(perfect match with index: {0})".format(index)


def translate_byte(one_byte_data, match, curr_state, record_len=0):
    if not curr_state:
        if one_byte_data[0] == "1":
            if "0" not in one_byte_data[1:]:
                return ("int_end", "Indexed: ...", 127)
            else:
                return ("end", "Indexed: {0}".format(int(one_byte_data[1:], base=2)), 0)
        elif one_byte_data[0:2] == "01":
            if "1" not in one_byte_data[2:]:
                return ("key_len", "Incremental Indexing -- New Name", 0)
            elif "0" not in one_byte_data[2:]:
                return ("int_value_len", "Incremental Indexing -- Indexed: ...", 63)
            else:
                return ("value_len", "Incremental Indexing -- Indexed: {0}".format(int(one_byte_data[2:], base=2)), 0)
        elif one_byte_data[0:4] == "0000":
            if "1" not in one_byte_data[4:]:
                return ("key_len", "without Indexing -- New Name", 0)
            elif "0" not in one_byte_data[4:]:
                return ("int_value_len", "without Indexing -- Indexed: ...", 15)
            else:
                return ("value_len", "without indexing -- indexed: {0}".format(int(one_byte_data[4:], base=2)))
        elif one_byte_data[0:4] == "0001":
            if "1" not in one_byte_data[4:]:
                return ("key_len", "never Indexing -- New Name", 0)
            elif "0" not in one_byte_data[4:]:
                return ("int_value_len", "never Indexing -- Indexed: ...", 15)
            else:
                return ("value_len", "never indexing -- indexed: {0}".format(int(one_byte_data[4:], base=2)))
        else:
            raise Exception(one_byte_data)

    if curr_state.startswith("int"):
        if "0" not in one_byte_data:
            record_len += 255
            return (curr_state, "int: 255", record_len)
        record_len += int(one_byte_data, base=2)
        return (curr_state[4:], "int sum: {0}".format(record_len), record_len)

    if curr_state.startswith("str"):
        record_len -= 1
        if record_len:
            return (curr_state, "", record_len)
        return (curr_state[4:], "", record_len)

    if curr_state == "key_len":
        huff = "huffman" if one_byte_data[0] == "1" else "non-huffman"
        if "0" not in one_byte_data[1:]:
            return ("int_str_value_len", "{0} key, len: ...".format(huff), 127)
        length = int(one_byte_data[1:], base=2)
        return ("str_value_len", "{0} key, len: {1}".format(huff, length), length)

    if curr_state == "value_len":
        huff = "huffman" if one_byte_data[0] == "1" else "non-huffman"
        if "0" not in one_byte_data[1:]:
            return ("int_str_end", "{0} value, len: ...".format(huff), 127)
        length = int(one_byte_data[1:], base=2)
        return ("str_end", "{0} value, len: {1}".format(huff, length), length)

    return ("state_failed", "state wrong: " + curr_state, 0)


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

            print "{0}=>{1}".format(header, binascii.hexlify(encoded), translate_match(match))
            print translate_match(match)

            curr_state = None
            length = 0
            for b in encoded:
                one_byte_data = bin(struct.unpack("B", b)[0])[2:].zfill(8)
                curr_state, content, length = translate_byte(one_byte_data, match, curr_state, length)
                if content:
                    print "{0} ({1})".format(one_byte_data, content)

            self.decoder.decode(encoded)
            print
        print "Decompressed from {0} to {1}".format(origin_len, encoded_len)

    def pretty_print_table(self, table):
        for (k, v) in table.dynamic_entries:
            print "{0}=>{1}".format(k, v)

    def tables(self):
        self.pretty_print_table(self.encoder.header_table)


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
