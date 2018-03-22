import pickle
import json
import argparse
import analysis
import torchvision
import os

from collections import Counter
from torch.autograd import Variable

PREVIOUS_ARRAY = None
LAST_EDGE_LAYER = 7 # 7 is cut at F.max_pool2d
TRAIN_DELTA_TREE = True
NUM_BINS = 60
FLAGS = None

def main():
    # train_huff_tree(delta_encoded_edge_output, 'delta_hist', write_to_json=True)
    run_edge_computation(FLAGS.video_file, write_to_json=True)
    # run_edge_computation("videos/n02676566/guitar_3.mp4")


def run_edge_computation(path_to_file, write = False, write_to_json = False):
    print('Running edge computation')
    # dumps frames into file
    fps, number_of_frames = analysis.get_fps_and_number_of_frames(path_to_file)
    PREVIOUS_ARRAY = None

    incept = torchvision.models.inception_v3(pretrained=True)
    incept.eval()

    for i in range(number_of_frames):
        img = analysis.read_in_frame_from_video(path_to_file, i * fps, write=write)

        edge_out = analysis.SplitComputation.forward(self=incept,
                                                     x=Variable(img),
                                                     start=0,
                                                     end=LAST_EDGE_LAYER)

        if PREVIOUS_ARRAY is not None and TRAIN_DELTA_TREE is True:
            input_to_compute_deltas = edge_out.data.numpy().squeeze(0)
            delta_edge_output = analysis.compute_delta(PREVIOUS_ARRAY, input_to_compute_deltas, 0.1)

            delta_encoded_edge_output = analysis.encode(delta_edge_output, min_num=-8,
                                                        max_num=8, num_bins=NUM_BINS)
            PREVIOUS_ARRAY = PREVIOUS_ARRAY - analysis.decode(delta_encoded_edge_output).squeeze(0)

            train_huff_tree(delta_encoded_edge_output, 'delta_hist', write_to_json= write_to_json)

        else:
            input_to_encoder = edge_out.data.numpy().squeeze(0)
            encoded_edge_output = analysis.encode(input_to_encoder, min_num=-8,
                                                  max_num=8, num_bins=NUM_BINS)
            train_huff_tree(encoded_edge_output, 'frame_one_hist', write_to_json=write_to_json)
            PREVIOUS_ARRAY = analysis.decode(encoded_edge_output).squeeze(0)


def train_huff_tree(array, file_name, write_to_json=False):
    print('Training huff tree dictionary')
    path = 'huffman_encoding_config/'+'layer'+str(LAST_EDGE_LAYER)+'/'+'num_bins_'+str(NUM_BINS)
    file_path = path+'/'+file_name
    # create path if does not exists
    if (os.path.isdir(path))is False:
        os.makedirs(path)
    try:
        with open(path + '.pickle', 'rb') as handle:
            hist = pickle.load(handle)
    except FileNotFoundError:
        print('No current histogram found')
        hist = Counter(range(-NUM_BINS, NUM_BINS))

    new_array = array.flatten().tolist()

    hist.update(new_array)

    with open(file_path+'.pickle', 'wb') as handle:
        pickle.dump(hist, handle, protocol=pickle.HIGHEST_PROTOCOL)

    if write_to_json is True:
        with open(file_path + '.json', 'w') as fp:
            json.dump(hist, fp)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--video_file',
        type=str,
        default='videos/test_vid.mp4',
        help='Absolute path to the folder storing the video to be analysed'
    )

    FLAGS, unparsed = parser.parse_known_args()
    main()
