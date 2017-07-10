from avutils import util
import sys
import os

class AbstractPerEpochCallback(object):

    def __call__(self, **kwargs):
        raise NotImplementedError()


class SaveBestValidModel(AbstractPerEpochCallback):

    def __init__(self, directory):
        self.directory = directory

    def  __call__(self, model_wrapper, is_new_best_valid_perf, **kwargs):
        if (is_new_best_valid_perf):
            model_wrapper.create_files_to_save(
                directory=self.directory,
                prefix="model_"+model_wrapper.random_string,
                update_last_saved=True)

class SuccessiveHalvingSaveBestValidModel(AbstractPerEpochCallback):
    def __init__(self, model_folder=None, **kwargs):
        self.model_folder = model_folder

    def save_model(self,model_wrapper):
        model_wrapper.create_files_to_save(
            directory=self.model_folder,
            prefix="bestModel",
            update_last_saved=True)

    def __call__(self, epoch, model_wrapper, valid_key_metric, train_key_metric,
    valid_all_stats, is_new_best_valid_perf, performance_history):
        if (is_new_best_valid_perf):
            self.save_model(model_wrapper)

class SaveModelSnapshot(AbstractPerEpochCallback):

    def __init__(self, prefix, directory):
        self.prefix = prefix
        self.directory = directory

    def  __call__(self, model_wrapper, epoch, **kwargs):
        model_wrapper.create_files_to_save(
            directory=self.directory+"/"+model_wrapper.random_string,
            prefix=self.prefix+"_epoch"+str(epoch)
                              +"_model_"+model_wrapper.random_string,
            update_last_saved=False)


class PrintPerfAfterEpoch(AbstractPerEpochCallback):

    def __init__(self, print_trend):
        #boolean controlling whether to print
        #what key metrics did in previous epochs
        self.print_trend = print_trend 

    def  __call__(self, epoch, valid_key_metric, train_key_metric,
                        valid_all_stats, performance_history, **kwargs):
        
        best_valid_perf_info = performance_history\
                               .get_best_valid_epoch_perf_info()
        best_valid_perf_epoch = best_valid_perf_info.epoch
        print("Finished epoch:\t"+str(epoch))
        print("Best valid perf epoch:\t"+str(best_valid_perf_epoch))
        print("Valid key metric:\t"+str(valid_key_metric))
        print("Train key metric:\t"+str(train_key_metric))
        print("Best valid perf info:")
        print(util.format_as_json(best_valid_perf_info.get_jsonable_object()))
        if (self.print_trend):
            valid_key_metric_trend = performance_history\
                                     .get_valid_key_metric_history()
            train_key_metric_trend = performance_history\
                                     .get_train_key_metric_history()
            print("epoch\ttrain\tvalid")
            for (epoch, (train_key_metric, valid_key_metric)) in\
                enumerate(zip(train_key_metric_trend,
                              valid_key_metric_trend)):
                print(str(epoch+1)+"\t"+str(train_key_metric)
                           +"\t"+str(valid_key_metric))
