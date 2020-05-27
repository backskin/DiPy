! / usr / bin / env
python3
# -*- coding: utf-8 -*-

"""
Author:         Dibyaranjan Sathua
Created on:     2019-02-28 12:26:54
"""

import tensorflow as tf
from tensorflow.tools.graph_transforms import TransformGraph
from tensorflow.core.framework import graph_pb2
import copy


def load_graph(filename):
    graph_def = tf.GraphDef()
    with tf.gfile.FastGFile(filename, 'rb') as f:
        graph_def.ParseFromString(f.read())
    return graph_def


def transform_graph(input_graph, output_graph=None):
    """ Use to run different transform function on the input graph and generate a output graph. """
    if isinstance(input_graph, graph_pb2.GraphDef):
        graph_def = input_graph
    else:
        graph_def = load_graph(input_graph)

    new_graph_def = TransformGraph(graph_def, ['input_placeholder/input_image'], ['predicated_output'],
                                   ['strip_unused_nodes(type=float, shape="1,28,28,1")',
                                    'remove_nodes(op=Identity, op=CheckNumerics, op=Switch)',
                                    'fold_constants(ignore_errors=true)', 'fold_batch_norms', 'fold_old_batch_norms',
                                    'sort_by_execution_order'])

    if output_graph == None:
        return new_graph_def

    # save new graph
    with tf.gfile.GFile(output_graph, "wb") as f:
        f.write(new_graph_def.SerializeToString())

    # tf.io.write_graph(od_graph_def, "", output_graph, as_text=False)


def convert_to_constant(input_graph, output_graph=None):
    """ Convert the placeholders in graph to constant nodes. """
    if isinstance(input_graph, graph_pb2.GraphDef):
        graph_def = input_graph
    else:
        graph_def = load_graph(input_graph)

    keep_prob = tf.constant(1.0, dtype=tf.float32, shape=[], name='keep_prob')
    weight_factor = tf.constant(1.0, dtype=tf.float32, shape=[], name='weight_factor')
    is_training = tf.constant(False, dtype=tf.bool, shape=[], name='is_training')

    new_graph_def = graph_pb2.GraphDef()

    for node in graph_def.node:
        if node.name == 'keep_prob':
            new_graph_def.node.extend([keep_prob.op.node_def])

        elif node.name == 'weight_factor':
            new_graph_def.node.extend([weight_factor.op.node_def])

        elif node.name == 'is_training':
            new_graph_def.node.extend([is_training.op.node_def])

        else:
            new_graph_def.node.extend([copy.deepcopy(node)])

    if output_graph == None:
        return new_graph_def

    # save new graph
    with tf.gfile.GFile(output_graph, "wb") as f:
        f.write(new_graph_def.SerializeToString())


def optimize_batch_normalization(input_graph, output_graph=None):
    """ Optimize the batch normalization block. """
    if isinstance(input_graph, graph_pb2.GraphDef):
        graph_def = input_graph
    else:
        graph_def = load_graph(input_graph)

    new_graph_def = graph_pb2.GraphDef()
    unused_attrs = ['is_training']  # Attributes of FusedBatchNorm. Not needed during inference.

    # All the node names are specific to my ocr model.
    # All the input names are found manually from tensorboard
    for node in graph_def.node:
        modified_node = copy.deepcopy(node)
        if node.name.startswith("conv"):  # True for Convolutional Layers
            starting_name = ""
            if node.name.startswith("conv1"):
                starting_name = "conv1"

            elif node.name.startswith("conv2"):
                starting_name = "conv2"

            elif node.name.startswith("conv3"):
                starting_name = "conv3"

            elif node.name.startswith("conv4"):
                starting_name = "conv4"

            # Do not add the cond block and its child nodes.
            # This is only needed during training.
            if "cond" in node.name and not node.name.endswith("FusedBatchNorm"):
                continue

            if node.op == "FusedBatchNorm" and node.name.endswith("FusedBatchNorm"):
                if bool(starting_name):
                    # Changing the name to remove one block hierarchy and changing inputs.
                    modified_node.name = "{0}/{0}/batch_norm/FusedBatchNorm".format(starting_name)
                    modified_node.input[0] = "{}/Conv2D".format(starting_name)
                    modified_node.input[1] = "{}/batch_norm/gamma".format(starting_name)
                    modified_node.input[2] = "{}/batch_norm/beta".format(starting_name)
                    modified_node.input[3] = "{}/batch_norm/moving_mean".format(starting_name)
                    modified_node.input[4] = "{}/batch_norm/moving_variance".format(starting_name)

                    # Deleting unused attributes
                    for attr in unused_attrs:
                        if attr in modified_node.attr:
                            del modified_node.attr[attr]

            if node.name.endswith('activation'):
                if bool(starting_name):
                    modified_node.input[0] = "{0}/{0}/batch_norm/FusedBatchNorm".format(starting_name)

        elif node.name.startswith("fc") or node.name.startswith("logits"):  # True for fully connected layers
            starting_name = ""
            if node.name.startswith("fc1"):
                starting_name = "fc1"

            elif node.name.startswith("fc2"):
                starting_name = "fc2"

            elif node.name.startswith("logits"):
                starting_name = "logits"

            # Do not add cond, cond_1 and moments block of batch normalization
            if "cond" in node.name or "moments" in node.name:
                continue

            # Change input of batchnorm/add
            if node.name.endswith('batchnorm/add'):
                modified_node.input[0] = "{}/batch_norm/moving_variance".format(starting_name)
                modified_node.input[1] = "{0}/{0}/batch_norm/batchnorm/add/y".format(starting_name)

            if node.name.endswith('batchnorm/mul_2'):
                modified_node.input[0] = "{0}/{0}/batch_norm/batchnorm/mul".format(starting_name)
                modified_node.input[1] = "{}/batch_norm/moving_mean".format(starting_name)

        new_graph_def.node.extend([modified_node])

    if output_graph == None:
        return new_graph_def

    # save the graph
    with tf.gfile.GFile(output_graph, "wb") as f:
        f.write(new_graph_def.SerializeToString())


def remove_dropout(input_graph, output_graph=None):
    """ Remove the dropout block from the model. """
    if isinstance(input_graph, graph_pb2.GraphDef):
        graph_def = input_graph
    else:
        graph_def = load_graph(input_graph)

    new_graph_def = graph_pb2.GraphDef()

    for node in graph_def.node:
        modified_node = copy.deepcopy(node)
        if node.name.startswith('dropout1') or node.name.startswith('dropout2'):
            continue

        if node.name == "fc2/fc2/batch_norm/batchnorm/mul_1":
            modified_node.input[0] = "mul"
            modified_node.input[1] = "fc2/weights"

        if node.name == "logits/logits/batch_norm/batchnorm/mul_1":
            modified_node.input[0] = "fc2/activation"
            modified_node.input[1] = "logits/weights"

        new_graph_def.node.extend([modified_node])

    if output_graph == None:
        return new_graph_def

    # save the graph
    with tf.gfile.GFile(output_graph, "wb") as f:
        f.write(new_graph_def.SerializeToString())


if __name__ == '__main__':
    # frozen_graph is the output of freeze_graph.py file
    frozen_graph = "frozen_inference_graph.pb"
    # Final graph file to be use with opencv dnn module
    output_graph = "frozen_inference_graph_dnn.pb"
    graph_def = transform_graph(frozen_graph)
    graph_def = convert_to_constant(graph_def)
    graph_def = optimize_batch_normalization(graph_def)
    graph_def = transform_graph(graph_def)
    remove_dropout(graph_def, output_graph)