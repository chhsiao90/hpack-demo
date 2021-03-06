# HPack Demo
A Demo project on how hpack process  
This project used [python-hyper/hpack](https://github.com/python-hyper/hpack) as the hpack encoder/decoder  
And used [http2jp/hpack-test-case](https://github.com/http2jp/hpack-test-case) for the test case  


## Install and Run
```shell
git clone https://github.com/chhsiao90/hpack-demo.git
pip install -r requirement.txt

# Run the simplest case
python demo.py story.json

# Select a case from hpack-test-case/raw-data and run it
python demo.py
```

## Core concept on hpack
- Encoder will use an index from static/dynamic table to represent a key-value header
- Encoder will index key-value header into dynamic table if it hadn't bean defined
- Decoder will decompressed index to original key-value header by searching static/dynamic table
- Deocder will set up dynamic table if new key-value received

## Core object on hpack
#### Encoder and Decoder
- Encoder crompressed the original header into binary format
- Decoder decompressed the binary format message back to original header
- Each server and client have one encoder and one decoder
- Each encoder corresponde to a decoder
    - Client->Encoder => Server->Decoder
    - Server->Encoder => Client->Decoder
- Encoder and Decoder is stateful because it contains a dynamic table

#### Static Table
- A list of key-value pair
- It's hardcode and fixed
- All decoder and encoder had one static table

#### Dynamic Table
- A list of key-value pair
- Used to cache header content had been used
- Each decoder and encoder had one dynamic table
- Server decoder's dynamic table will same as client encoder's dynamic table
- Client decoder's dynamic table will same as server encoder's dynamic table

## In binary
#### First byte
- 1XXXXXXX: Indexd Header
- 01XXXXXX: Literal Header with Indexing
- 0000XXXX: Literal Header without Indexing
- 0001XXXX: Literal Header never Indexing

#### Indexing
**Get Index Value**
- Convert the remain bits of first byte to integer.
- If all of the remain bits of first byte is 1, add next bytes till the byte that contains 0

**Index = 0**
- No entry in static table or dynamic table
- following content would be Name

**0 < Index <= 61**
- Has entry in static table
- following content would be value

**Index > 61**
- Has entry in dynamic table
- following content would be value

#### Length
- Summarize every byte till the byte that contains 0

#### Name
**First Bit**  
- 1 = Huffman  
- 0 = Non-Huffman

**Get Length**  
- Check Length Block

**Following Bytes**  
- Following Length bytes is the name

#### Value
**First Bit**  
- 1 = Huffman  
- 0 = Non-Huffman  

**Get Length**  
- Check Length Block

**Following Bytes**  
- Following Length bytes is the value

## Screenshot
![gif](http://i.imgur.com/2LcmrO2.gif)
