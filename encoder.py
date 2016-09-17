import sys
import os
import h5py
import json
import gzip


class Encoder(object):
    """Encoder class.
    Weights are serialized sequentially from the Keras flattened_layers representation
    into:
        - `weights`: a binary string representing the raw data bytes in float32
            of all weights, sequentially concatenated.
        - `metadata`: a list containing the byte length and tensor shape,
            so that the original tensors can be reconstructed
    """

    def __init__(self, weights_hdf5_filepath):
        if not weights_hdf5_filepath:
            raise Exception('weights_hdf5_filepath must be defined.')
        self.weights_hdf5_filepath = weights_hdf5_filepath
        self.weights = b''
        self.metadata = []

    def serialize(self):
        """serialize method.
        Strategy for extracting the weights is adapted from the
        load_weights_from_hdf5_group method of the Container class:
        see https://github.com/fchollet/keras/blob/master/keras/engine/topology.py#L2505-L2585
        """
        hdf5_file = h5py.File(self.weights_hdf5_filepath, mode='r')
        f = hdf5_file['model_weights']

        layer_names = [n.decode('utf8') for n in f.attrs['layer_names']]
        for layer_name in layer_names:
            g = f[layer_name]
            weight_names = [n.decode('utf8') for n in g.attrs['weight_names']]
            if len(weight_names):
                for weight_name in weight_names:
                    meta = {}
                    meta['layer_name'] = layer_name
                    meta['weight_name'] = weight_name
                    weight_value = g[weight_name].value
                    bytearr = weight_value.tobytes()
                    self.weights += bytearr
                    meta['size'] = len(bytearr)
                    meta['shape'] = list(weight_value.shape)
                    meta['type'] = 'float32'
                    self.metadata.append(meta)

        hdf5_file.close()

    def save(self):
        """Saves weights data (gzipped binary) and weights metadata (json)
        """
        weights_filepath = '{}_weights.buf.gz'.format(os.path.splitext(self.weights_hdf5_filepath)[0])
        with gzip.open(weights_filepath, mode='wb', compresslevel=9) as f:
            f.write(self.weights)
        metadata_filepath = '{}_metadata.json'.format(os.path.splitext(self.weights_hdf5_filepath)[0])
        with open(metadata_filepath, mode='w') as f:
            json.dump(self.metadata, f)


if __name__ == '__main__':
    """Usage:
        python encoder.py example.hdf5

    Output:
        - example_weights.buf.gz
        - example_metadata.json
    """
    encoder = Encoder(*sys.argv[1:])
    encoder.serialize()
    encoder.save()
