from __future__ import division
import os
import time
from glob import glob
import tensorflow as tf
import pickle
from six.moves import xrange
from scipy.stats import entropy

from ops import *
from utils import *
class GAN(object):
    def __init__(self, sess, image_size=64, is_crop=False,
                 batch_size=64, text_vector_dim=100,
                 z_dim=100, t_dim=256, gf_dim=64, df_dim=64, c_dim=3,
                 checkpoint_dir=None, sample_dir=None, log_dir=None, 
                 lam1=0.1, lam2=0.1, lam3=0.1):
                  """

        Args:
            sess: TensorFlow session
            batch_size: The size of batch. Should be specified before training.
            z_dim: (optional) Dimension of dim for Z. [100]
            t_dim: (optional) Dimension of text features. [256]
            gf_dim: (optional) Dimension of gen filters in first conv layer. [64]
            df_dim: (optional) Dimension of discrim filters in first conv layer. [64]
            c_dim: (optional) Dimension of image color. [3]
            lam1: (optional) Hyperparameter for contextual loss. [0.1]
            lam2: (optional) Hyperparameter for perceptual loss. [0.1]
            lam3: (optional) Hyperparameter for wrong examples [0.1]
        """
        self.sess = sess
        self.is_crop = is_crop
        self.batch_size = batch_size
        self.text_vector_dim = text_vector_dim
        self.image_size = image_size
        self.image_shape = [image_size, image_size * 2, 3]
        # self.image_shape = [image_size, image_size, 3]

        self.sample_freq = int(100*64/batch_size)
        self.save_freq = int(500*64/batch_size)

        self.z_dim = z_dim
        self.t_dim = t_dim

        self.gf_dim = gf_dim
        self.df_dim = df_dim

        self.lam1 = lam1
        self.lam2 = lam2
        self.lam3 = lam3

        self.c_dim = 3

        # batch normalization : deals with poor initialization helps gradient flow
        self.d_bn1 = batch_norm(name='d_bn1')
        self.d_bn2 = batch_norm(name='d_bn2')
        self.d_bn3 = batch_norm(name='d_bn3')
        self.d_bn4 = batch_norm(name='d_bn4')

        self.g_bn0 = batch_norm(name='g_bn0')
        self.g_bn1 = batch_norm(name='g_bn1')
        self.g_bn2 = batch_norm(name='g_bn2')
        self.g_bn3 = batch_norm(name='g_bn3')

        self.checkpoint_dir = checkpoint_dir
        self.sample_dir = sample_dir
        self.log_dir = log_dir
        
        #self.build_model()

        self.model_name = "GAN"

    def discriminator(self, image, t, reuse=False):
        if reuse:
            tf.get_variable_scope().reuse_variables()

        h0 = lrelu(conv2d(image, self.df_dim, name='d_h0_conv'))
        
        t_ = tf.expand_dims(t, 1)
        t_ = tf.expand_dims(t_, 2)
        t_tiled = tf.tile(t_, [1,32,64,1], name='tiled_t')
        h0_concat = tf.concat( [h0, t_tiled],3, name='h0_concat')
        
        h1 = lrelu(self.d_bn1(conv2d(h0_concat, self.df_dim*2, name='d_h1_conv')))
        h2 = lrelu(self.d_bn2(conv2d(h1, self.df_dim*4, name='d_h2_conv')))
        h3 = lrelu(self.d_bn3(conv2d(h2, self.df_dim*8, name='d_h3_conv')))

        #h4 = linear(tf.reshape(h3, [-1, 8192*2]), 1, 'd_h3_lin')
        # conv to 512x1x1
        h4 = conv2d(h3, self.df_dim*8, 4, 8, 1, 1, name='d_h4_conv')
        
        return tf.nn.sigmoid(h4), h4

    
    def generator(self, z, t):
        
        self.z_, self.h0_lin_w, self.h0_lin_b = linear(z, self.gf_dim*4*8, 'g_h0_lin', with_w=True)
        z_ = tf.reshape(self.z_, [-1, 4, 8, self.gf_dim])
        
        t_ = tf.expand_dims(tf.expand_dims(t, 1), 2)
        t_tiled = tf.tile(t_, [1,4,8,1])
        
        h0_concat = tf.concat( [z_, t_tiled],3)
        
        self.h0, self.h0_w, self.h0_b = conv2d_transpose(h0_concat,
            [self.batch_size, 4, 8, self.gf_dim*8], 1, 1, 1, 1, name='g_h0', with_w=True)
        h0 = tf.nn.relu(self.g_bn0(self.h0))
        
        self.h1, self.h1_w, self.h1_b = conv2d_transpose(h0,
            [self.batch_size, 8, 16, self.gf_dim*4], name='g_h1', with_w=True)
        h1 = tf.nn.relu(self.g_bn1(self.h1))

        h2, self.h2_w, self.h2_b = conv2d_transpose(h1,
            [self.batch_size, 16, 32, self.gf_dim*2], name='g_h2', with_w=True)
        h2 = tf.nn.relu(self.g_bn2(h2))

        h3, self.h3_w, self.h3_b = conv2d_transpose(h2,
            [self.batch_size, 32, 64, self.gf_dim*1], name='g_h3', with_w=True)
        h3 = tf.nn.relu(self.g_bn3(h3))

        h4, self.h4_w, self.h4_b = conv2d_transpose(h3,
            [self.batch_size, 64, 128, 3], name='g_h4', with_w=True)

        return tf.nn.tanh(h4)