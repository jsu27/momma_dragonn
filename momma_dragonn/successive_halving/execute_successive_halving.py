'''
Created on Jun 16, 2017

@author: evaprakash
'''
import json
import yaml
import os
from shutil import copyfile
import subprocess
from subprocess import CalledProcessError
import json
import math
from collections import OrderedDict
import sys


def execute_command(command, use_shell=False):
    process = subprocess.Popen(command, shell=use_shell, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    # Poll process for new output until finished
    while True:
        nextline = process.stdout.readline()
        if nextline == '' and process.poll() is not None:
            break
        sys.stdout.write(nextline)
        sys.stdout.flush()
    output = process.communicate()[0]
    exitCode = process.returncode
    if (exitCode == 0):
        return output
    else:
        raise CalledProcessError(command, exitCode, output)

class RunSuccessiveHalving(object):
    def __init__(self):
        pass

    def calculate_iterations(self, number_models):
        raw_log = math.log(number_models, 2)
        iterations = int(math.ceil(raw_log) + 1.0)
        return iterations

    def print_successive_halving_info(self, iterations, starting_epochs, number_models):
        print("Successive halving starting epochs: "+str(starting_epochs))
        print("Successive halving total iterations: " + str(iterations))
        print("Successive halving number of models: " + str(number_models))
        print("Successive halving total epochs for best model: " + str(starting_epochs*((2**iterations)-1)))
        print("Successive halving total epochs for all models: " + str(starting_epochs*number_models*iterations))

    def __call__(self):
        models_info_file=open("models_info.json","r")
        models_info=json.load(models_info_file)
        number_models=len(models_info["model_creators"])
        epochs = int(models_info["successive_halving_info"]["starting_epochs"])
        base_epoch = 0
        total_iterations = self.calculate_iterations(number_models)
        self.print_successive_halving_info(iterations=total_iterations,starting_epochs=epochs,number_models=number_models)
        model_list=[]
        for n in range (0,number_models):
            model_list.append(str(n))
        for current_iteration in range(0, total_iterations):
            print "Successive halving: starting iteration number " + str(current_iteration+1) + \
                  ", base epoch "  +  str(base_epoch) + ", will run for " + str(epochs) + " epochs"
            sh=RunSuccessiveHalvingIteration(epochs, model_list, base_epoch)
            model_list=sh()
            print "Successive halving: completed iteration number " + str(current_iteration+1)
            base_epoch = base_epoch + epochs
            epochs*=2

class RunSuccessiveHalvingIteration(object):
    def __init__(self, epochs, model_list, base_epoch):
        self.epochs = epochs
        self.model_list = model_list
        self.base_epoch = base_epoch

    def __call__(self):
        for model in self.model_list:
            self.update_epoch_and_base_epoch_in_hyperparams(model)
            self.execute_momma_dragonn(model)
        return self.select_winners()


    def update_epoch_and_base_epoch_in_hyperparams(self, model):
        hyperparams_file=open("model"+str(model)+"/hyperparameter_configs_list.yaml","r")
        hyperparams_list=yaml.load(hyperparams_file)
        hyperparams_list[0]["model_trainer"]["kwargs"]["stopping_criterion_config"]["kwargs"]["max_epochs"]=self.epochs
        hyperparams_list[0]["model_trainer"]["kwargs"]["base_epoch"]=self.base_epoch
        hyperparams_file.close()
        hyperparams_file = open("model" + str(model) + "/hyperparameter_configs_list.yaml", "w")
        json.dump(hyperparams_list, hyperparams_file, indent=4)
        hyperparams_file.close()


    def execute_momma_dragonn(self, model):
        command_line = ["momma_dragonn_train","--hyperparameter_configs_list=model" + str(model) + "/hyperparameter_configs_list.yaml",
        "--valid_data_loader_config=valid_data_loader_config.yaml", "--evaluator_config=evaluator_config.yaml",
        "--end_of_epoch_callbacks_config=model" + str(model) + "/end_of_epoch_callbacks_config.yaml",
        "--end_of_training_callbacks_config=model" + str(model) + "/end_of_training_callbacks_config.yaml"]
        print "About to call model " + str(model) + " with command:\n" + str(command_line)
        execute_command(command_line)
        print "Done running model" +str(model)

    def print_selections(self, sorted_models_performance, number_selected, selected_models):
        print("Successive halving sorted models performance:" + str(sorted_models_performance))
        print("Successive halving number of models selected:" + str(number_selected))
        print("Successive halving selected models:" + str(selected_models))

    def select_winners(self):
        #Based on files generated by end of training callbacks, gather all model metrics in list.
        #When list is made, use .sort() to get top half or bottom half of metrics (make new list), depending on metric
        #New list = winners
        models_performance = dict()
        for model in self.model_list:
            models_performance[str(model)] = self.get_best_perf(model)
        sorted_models_performance = OrderedDict(sorted(models_performance.items(), key =lambda x: x[1], reverse = True))
        number_to_select = int(math.ceil(len(sorted_models_performance)/2))
        selected_models=sorted_models_performance.keys()[:number_to_select]
        self.print_selections(sorted_models_performance=sorted_models_performance,number_selected=number_to_select,selected_models=selected_models)
        return selected_models

    def get_best_perf(self, model):
        performance_history_file=open("model"+str(model)+"/initial_performance_history.json","r")
        performance_history_file_content=json.load(performance_history_file)
        performance_history_file.close()
        return float(performance_history_file_content["best_valid_epoch_perf_info"]["valid_key_metric"])










