import socket
import sys
import numpy as np
import torch
import pickle
import json
import os

from dahuffman import HuffmanCodec
from analysis import server_run, decode_delta, decode, load_huff_dictionary

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to the port
server_address = ('localhost', 10000)
print(sys.stderr, 'starting up on %s port %s' % server_address)
sock.bind(server_address)

# Listen for incoming connections
sock.listen(1)
connect = True
failCount = 0
passCount = 0
PREVIOUS_ARRAY = None

# These values should be the same on the server side
USE_DELTA = True
LAST_EDGE_LAYER = 7
NUM_BINS = 60
DELTA_VALUE = 0.1

RESHAPE_ARRAY_DIMENSIONS = [192, 35, 35]

codec_path = 'huffman_encoding_config/' + 'layer' + str(LAST_EDGE_LAYER) + '/' + 'num_bins_' + str(NUM_BINS)
delta_hist = load_huff_dictionary(codec_path + '/delta_hist')
delta_codec = HuffmanCodec.from_frequencies(delta_hist)
frame_one_hist = load_huff_dictionary(codec_path + '/frame_one_hist')
frame_one_codec = HuffmanCodec.from_frequencies(frame_one_hist)

sizes = []
videos = [
    "videos/n01443537/goldfish_1.mp4",
    "videos/n01443537/goldfish_2.mp4",
    "videos/n01443537/goldfish_3.mp4",

    "videos/n01882714/koala_1.mp4",
    "videos/n01882714/koala_2.mp4",
    "videos/n01882714/koala_3.mp4",

    "videos/n02085620/dog_1.mp4",

    "videos/n02099601/golden_retriever_1.mp4",

    "videos/n02099712/golden_retriever_1.mp4",

    "videos/n02110958/pug_1.mp4",
    "videos/n02110958/pug_3.mp4",
    "videos/n02110958/pug_4.mp4",

    "videos/n02206856/bee_1.mp4",

    "videos/n02391049/zebra_1.mp4",
    "videos/n02391049/zebra_2.mp4",
    "videos/n02391049/zebra_3.mp4",

    "videos/n02510455/panda_1.mp4",
    "videos/n02510455/panda_2.mp4",
    "videos/n02510455/panda_3.mp4",
    "videos/n02510455/panda_4.mp4",
    "videos/n02510455/panda_5.mp4",

    "videos/n02676566/guitar_1.mp4",
    "videos/n02676566/guitar_2.mp4",
    "videos/n02676566/guitar_3.mp4",
    "videos/n02676566/guitar_4.mp4",
    "videos/n02676566/guitar_6.mp4",

    "videos/n02787622/banjo_1.mp4",
    "videos/n02787622/banjo_2.mp4",
    "videos/n02787622/banjo_3.mp4",
    "videos/n02787622/banjo_5.mp4",

    "videos/n03452741/piano_1.mp4",
    "videos/n03452741/piano_2.mp4",

    "videos/n03495258/harp_1.mp4",
    "videos/n03495258/harp_2.mp4",
    "videos/n03495258/harp_3.mp4",

    "videos/n03584254/ipod_1.mp4",
    "videos/n03584254/ipod_2.mp4",

    "videos/n03967562/plough_1.mp4",

    "videos/n04536866/violin_3.mp4",
    "videos/n04536866/violin_4.mp4",

    "videos/n06596364/comic_1.mp4",

    "videos/n01910747/jelly_fish_1.mp4",
    "videos/n01910747/jelly_fish_2.mp4",

    "videos/n02134084/polar_bear_1.mp4",
    "videos/n02134084/polar_bear_3.mp4",

    "videos/n02342885/hamster_1.mp4",
    "videos/n02342885/hamster_2.mp4",
    "videos/n02342885/hamster_4.mp4",
    "videos/n02342885/hamster_5.mp4",

    "videos/n02364673/guinea_pig_1.mp4",
    "videos/n02364673/guinea_pig_2.mp4"
]
vid_num = 0

# NEED TO CHECK THIS CODE WORKS FOR AUTOMATED TESTING
cats = json.load(open('config/categories.json'))
class_id = videos[vid_num].split('/')[1]
for j in range(len(cats)):
    if cats[j]['id'] == class_id:
        index = cats[j]['index']

while True:
    # Wait for a connection
    received = ''
    arr = bytearray()
    byte_size = 0

    print(sys.stderr, 'waiting for a connection')
    connection, client_address = sock.accept()

    try:
        print(sys.stderr, 'connection from', client_address)

        # Receive the data in small chunks and retransmit it
        while True:
            data = connection.recv(1024)
            byte_size = byte_size + len(data)
            # received = received + (data.decode('utf-8'))
            arr.extend(data)
            # print(sys.stderr, 'received "%s"' % data)
            if data:
                # print(sys.stderr, 'sending data back to the client')
                connection.sendall(data)
            else:
                print(sys.stderr, 'no more data from', client_address)
                connect = False
                break

    finally:
        # Clean up the connection
        connection.close()
        print('Size of data received: ', byte_size)

        # code for reveving reset to frame one
        if byte_size == 1:
            print('Recieved reset')
            avg_byte_size = sum(sizes) / len(sizes)
            passRate = (passCount / (failCount + passCount)) * 100
            print('percentage of passed: ', passRate)
            result = 'file: ' + videos[vid_num] + ', %Passed: ' + str(passRate) + ', avg_byte_size: ' \
                     + str(avg_byte_size) + ', layer: ' + str(LAST_EDGE_LAYER) + ', num_bins_used: ' + str(NUM_BINS) + \
                     ', Delta Value: ' + str(DELTA_VALUE) + '\n'
            results_path = "Results" + '/layer' + str(LAST_EDGE_LAYER) + '/num_bins_' + str(NUM_BINS) + '/delta_value' \
                           + str(DELTA_VALUE)
            if not os.path.isdir(results_path):
                os.makedirs(results_path)
            with open(results_path + "/results.txt", "a") as myfile:
                myfile.write(result)

            # Resetting variables
            PREVIOUS_ARRAY = None
            sizes = []
            passCount = 0
            failCount = 0
            vid_num += 1

            # NEED TO ENSURE THIS CODE WORKS FOR AUTOMATED TESTING
            cats = json.load(open('config/categories.json'))
            class_id = videos[vid_num].split('/')[1]
            for j in range(len(cats)):
                if cats[j]['id'] == class_id:
                    index = cats[j]['index']

        # print('Recieved: ', arr)
        elif PREVIOUS_ARRAY is not None and USE_DELTA is True:
            # new code
            decoded = delta_codec.decode(arr)
            arr = np.reshape(decoded, [192, 35, 35])

            decoded_arr = decode(arr, NUM_BINS, max_num=8, min_num=-8)
            delta_decoded_arr = decode_delta(PREVIOUS_ARRAY, decoded_arr)
            # print(delta_decoded_arr)
            PREVIOUS_ARRAY = delta_decoded_arr
            result = server_run(torch.Tensor(delta_decoded_arr), LAST_EDGE_LAYER, class_label=index)
        else:
            # new code
            decoded = frame_one_codec.decode(arr)
            arr = np.reshape(decoded, [192, 35, 35])

            decoded_arr = decode(arr, NUM_BINS, max_num=8, min_num=-8)
            PREVIOUS_ARRAY = decoded_arr
            result = server_run(torch.Tensor(decoded_arr), LAST_EDGE_LAYER, class_label=index)

        if result:
            passCount += 1
        else:
            failCount += 1
        sizes.append(byte_size)
        print('Total checked: ', passCount + failCount)
        print('Number of correct classifictaions: ', passCount)
        print('Number Failed: ', failCount)
