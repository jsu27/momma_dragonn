from momma_dragonn.loaders import load_class_from_config
from collections import OrderedDict

class AbstractReparameterizer(object):

    def __call__(self, model):
        raise NotImplementedError()

    def get_jsonable_object(self):
        raise NotImplementedError()


class CollapseFirstTwoKerasConv(object):

    def __init__(self, reparam_epoch, optimizer_config, loss, metrics=[]):
        self.reparam_epoch = reparam_epoch
        self.optimizer_config = optimizer_config
        self.loss = loss
        self.metrics = metrics

    def get_jsonable_object(self):
        return OrderedDict([('class',str(type(self)),
                            ('reparam_epoch',reparam_epoch),
                            ('optimizer_config',self.optimizer_config),
                            ('loss', self.loss)])

    def _compile_model(self, model):
        optimizer = load_class_from_config(self.optimizer_config)
        if (isinstance(self.loss, str)):
            loss = self.loss
        else:
            loss = load_class_from_config(self.loss) 
        model.compile(optimizer=optimizer, loss=loss, metrics=self.metrics) 

    def do_reparameterization(self, epoch, **kwargs):
        return epoch==self.reparam_epoch

    def __call__(self, model):
        # figure out old conv layers
        config1 = model.layers[0].get_config()
        config2 = model.layers[1].get_config()
        W1 = model.layers[0].get_weights()[0]
        W2 = model.layers[1].get_weights()[0]

        filters = config2['filters']
        kernel_size = config1['kernel_size'][0] + config2['kernel_size'][0] - 1
        padding = config2['padding']
        activation = config2['activation']
        strides = config2['strides']
        input_shape = config1['batch_input_shape'][1:]

        # set up new conv layer
        new_model = Sequential()
        new_model.add(Conv1D(input_shape=input_shape,
                             filters=filters,
                             kernel_size=kernel_size,
                             padding=padding,
                             activation=activation,
                             strides=strides))

        # get weights for new conv layer
        new_l, new_c, new_f = new_model.layers[0].get_weights()[0].shape
        new_W = np.zeros((new_l, new_c, new_f))
        new_W = compute_equivalent_weights(W1, W2, new_W)

        # get bias for new conv layer
        new_b = model.layers[1].get_weights()[1]

        # set weight and bias
        new_model.layers[0].set_weights((new_W, new_b))

        # copy over rest of model
        for layer in model.layers[2:]:
            new_layer = layer.__class__.from_config(layer.get_config())
            new_layer.build(layer.input_shape)
            #print(new_layer.weights)
            #print(layer.weights)
            new_layer.set_weights(layer.get_weights())
            new_model.add(new_layer)

        self._compile_model(new_model)

        return new_model 
