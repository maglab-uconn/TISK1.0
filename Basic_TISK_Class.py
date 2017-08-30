#########################################################
# TISK 1.x Distribution by Heejo You, based on code
# developed by Thomas Hannagan implementing the original
# TISK model (Hannagan, Magnuson & Grainger, 2013). This
# distribution was re-implemented from scratch in 2016-17
# in Jim Magnuson's lab at the University of Connecticut.
#
# The most current version of the software should always
# be available at https://github.com/CODEJIN/TISK
#
# The github repository includes a brief guide (PDF file)
# to help get you started.
#
#
# TISK 1.x Distribution
# Copyright (C) 2017 Heejo You and James Magnuson
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#########################################################

import numpy as np;
import matplotlib.pyplot as plt;
import time;
import os;

def List_Generate():
    word_List = [];
    with open("Pronunciation_Data.txt") as f:
        readLines = f.readlines();
        for readLine in readLines:
            word_List.append(readLine.replace("\n",""));

    phoneme_Set = set();
    for word in word_List:
        phoneme_Set.update(set(word));

    if os.path.isfile("Phoneme_Data.txt"):
        with open("Phoneme_Data.txt") as f:
            readLines = f.readlines();
            for readLine in readLines:
                phoneme_Set.add(readLine.replace("\n",""));

    return list(phoneme_Set), word_List;

class TISK_Model:
    def __init__(self, phoneme_List, word_List, time_Slot = None, threshold = None):
        #Assign Label
        self.phoneme_List = phoneme_List;
        self.diphone_List = [];
        for first_Diphone in phoneme_List:
            for second_Diphone in phoneme_List:
                self.diphone_List.append(first_Diphone + second_Diphone);
        self.single_Phone_List = phoneme_List.copy();
        self.word_List = word_List;

        self.phoneme_Amount = len(self.phoneme_List);
        self.diphone_Amount = len(self.diphone_List);
        self.word_Amount = len(self.word_List);

        self.parameter_Dict = {};
        self.parameter_Dict[("Length", "IStep")] = 10;
        max_Word_Length = max([len(x) for x in self.word_List]);
        if time_Slot is None:
            self.parameter_Dict[("Length", "Time_Slot")] = max_Word_Length;
        elif time_Slot < max_Word_Length:
            raise Exception("Assigned time slot is lower than the length of the longest word");
        else:
            self.parameter_Dict[("Length", "Time_Slot")] = time_Slot;

        if threshold is None:
            self.parameter_Dict[("Length", "Threshold")] = (self.parameter_Dict[("Length", "IStep")] * (self.parameter_Dict[("Length", "Time_Slot")] - 1) + 1) / (self.parameter_Dict[("Length", "IStep")] * self.parameter_Dict[("Length", "Time_Slot")]);
        else:
            self.parameter_Dict[("Length", "Threshold")] = threshold;

        self.Decay_Parameter_Assign(0.001, 0.001, 0.001, 0.01);
        self.Weight_Parameter_Assign(1.0, 0.1, 0.05, 0.01, -0.005);
        self.Feedback_Parameter_Assign(0.0, 0.0, 0.0, 0.0);

    def Decay_Parameter_Assign(self, decay_Phoneme = None, decay_Diphone = None, decay_SPhone = None, decay_Word = None):
        if decay_Phoneme is not None:
            self.parameter_Dict[("Decay", "Phoneme")] = decay_Phoneme;
        if decay_Diphone is not None:
            self.parameter_Dict[("Decay", "Diphone")] = decay_Diphone;
        if decay_SPhone is not None:
            self.parameter_Dict[("Decay", "SPhone")] = decay_SPhone;
        if decay_Word is not None:
            self.parameter_Dict[("Decay", "Word")] = decay_Word;

    def Weight_Parameter_Assign(self, input_to_Phoneme_Weight = None, phoneme_to_Phone_Weight = None, diphone_to_Word_Weight = None, sPhone_to_Word_Weight = None, word_to_Word_Weight = None):
        if input_to_Phoneme_Weight is not None:
            self.parameter_Dict[("Weight", "Input_to_Phoneme")] = input_to_Phoneme_Weight;
        if phoneme_to_Phone_Weight is not None:
            self.parameter_Dict[("Weight", "Phoneme_to_Phone")] = phoneme_to_Phone_Weight;
        if diphone_to_Word_Weight is not None:
            self.parameter_Dict[("Weight", "Diphone_to_Word")] = diphone_to_Word_Weight;
        if sPhone_to_Word_Weight is not None:
            self.parameter_Dict[("Weight", "SPhone_to_Word")] = sPhone_to_Word_Weight;
        if word_to_Word_Weight is not None:
            self.parameter_Dict[("Weight", "Word_to_Word")] = word_to_Word_Weight;

        self.initialized = False;

        if self.parameter_Dict[("Weight", "Phoneme_to_Phone")] * self.parameter_Dict[("Length", "Time_Slot")] <= self.parameter_Dict[("Length", "Threshold")]:
            print("Phoneme to Phone Weight: " + str(self.parameter_Dict[("Weight", "Phoneme_to_Phone")]));
            print("Time Slot: " + str(self.parameter_Dict[("Length", "Time_Slot")]))
            print("Threshold: " + str(self.parameter_Dict[("Length", "Threshold")]))
            print("It is recommanded that the value multiplied by 'Phoneme to Phone weight' and 'Time Slot' is greater than 'Threshold'.");

    def Feedback_Parameter_Assign(self, word_to_Diphone_Activation = None, word_to_SPhone_Activation = None, word_to_Diphone_Inhibition = None, word_to_SPhone_Inhibition = None):
        if word_to_Diphone_Activation is not None:
            self.parameter_Dict[("Feedback", "Word_to_Diphone_Activation")] = word_to_Diphone_Activation;
        if word_to_SPhone_Activation is not None:
            self.parameter_Dict[("Feedback", "Word_to_SPhone_Activation")] = word_to_SPhone_Activation;
        if word_to_Diphone_Inhibition is not None:
            self.parameter_Dict[("Feedback", "Word_to_Diphone_Inhibition")] = word_to_Diphone_Inhibition;
        if word_to_SPhone_Inhibition is not None:
            self.parameter_Dict[("Feedback", "Word_to_SPhone_Inhibition")] = word_to_SPhone_Inhibition;

        self.initialized = False;

    def Weight_Initialize(self):
        #Weight Generate
        self.weightMatrix_Phoneme_to_Diphone = np.zeros(shape=(self.phoneme_Amount * self.parameter_Dict[("Length", "Time_Slot")], self.diphone_Amount));
        self.weightMatrix_Phoneme_to_Single_Phone = np.zeros(shape=(self.phoneme_Amount * self.parameter_Dict[("Length", "Time_Slot")], self.phoneme_Amount));
        self.weightMatrix_Diphone_to_Word = np.zeros(shape=(self.diphone_Amount, self.word_Amount));
        self.weightMatrix_Single_Phone_to_Word = np.zeros(shape=(self.phoneme_Amount, self.word_Amount));
        self.weightMatrix_Word_to_Word = np.zeros(shape=(self.word_Amount, self.word_Amount));
        self.weightMatrix_Word_to_Diphone = np.zeros(shape=(self.word_Amount, self.diphone_Amount));
        self.weightMatrix_Word_to_Single_Phone = np.zeros(shape=(self.word_Amount, self.phoneme_Amount));

        #Weight Connection
        #Phoneme -> Diphone & Single phone
        for slot_Index in range(self.parameter_Dict[("Length", "Time_Slot")]):
            for phoneme_Index in range(self.phoneme_Amount):
                for diphone_Index in range(self.diphone_Amount):
                    if self.phoneme_List[phoneme_Index] == self.diphone_List[diphone_Index][0]:
                        self.weightMatrix_Phoneme_to_Diphone[slot_Index * self.phoneme_Amount + phoneme_Index, diphone_Index] += self.parameter_Dict[("Weight", "Phoneme_to_Phone")] * (self.parameter_Dict[("Length", "Time_Slot")] - 1 - slot_Index);    #When slot is more later, weight decrease more.
                    if self.phoneme_List[phoneme_Index] == self.diphone_List[diphone_Index][1]:
                        self.weightMatrix_Phoneme_to_Diphone[slot_Index * self.phoneme_Amount + phoneme_Index, diphone_Index] += self.parameter_Dict[("Weight", "Phoneme_to_Phone")] * slot_Index; #When slot is more later, weight increase more.
                for single_Phone_Index in range(self.phoneme_Amount):
                    if self.phoneme_List[phoneme_Index] == self.single_Phone_List[single_Phone_Index]:
                        self.weightMatrix_Phoneme_to_Single_Phone[slot_Index * self.phoneme_Amount + phoneme_Index, single_Phone_Index] += self.parameter_Dict[("Weight", "Phoneme_to_Phone")] * self.parameter_Dict[("Length", "Time_Slot")];    #Always weight become 1

        ##Diphone -> Word
        for diphone_Index in range(self.diphone_Amount):
            for word_Index in range(self.word_Amount):
                if self.diphone_List[diphone_Index] in self.Open_Diphone_Generate(self.word_List[word_Index]):
                    self.weightMatrix_Diphone_to_Word[diphone_Index, word_Index] = self.parameter_Dict[("Weight", "Diphone_to_Word")] / len(self.word_List[word_Index]);   #Divide by the length of pronunciation

        ##Single phone -> Word
        for single_Phone_Index in range(self.phoneme_Amount):
            for word_Index in range(self.word_Amount):
                if self.single_Phone_List[single_Phone_Index] in self.word_List[word_Index]:
                    self.weightMatrix_Single_Phone_to_Word[single_Phone_Index, word_Index] = self.parameter_Dict[("Weight", "SPhone_to_Word")]; #Always weight become 0.01

        ##Word -> Word (Inhibition)
        for word1_Index in range(self.word_Amount):
            for word2_Index in range(self.word_Amount):
                word1_Feature = set([self.word_List[word1_Index][x:x+2] for x in range(len(self.word_List[word1_Index]) - 1)] + list(self.word_List[word1_Index]));
                word2_Feature = set([self.word_List[word2_Index][x:x+2] for x in range(len(self.word_List[word2_Index]) - 1)] + list(self.word_List[word2_Index]));

                intersection = word1_Feature & word2_Feature;
                self.weightMatrix_Word_to_Word[word1_Index, word2_Index] = len(intersection) * self.parameter_Dict[("Weight", "Word_to_Word")]; # shared feature is more, the inhibition also become stronger
        for word_Index in range(self.word_Amount):
            self.weightMatrix_Word_to_Word[word_Index, word_Index] = 0; # self inhibtion is 0

        ##Word -> Diphone & Single Phone
        for word_Index in range(self.word_Amount):
            for diphone_Index in range(self.diphone_Amount):
                if self.diphone_List[diphone_Index] in self.Open_Diphone_Generate(self.word_List[word_Index]):
                    self.weightMatrix_Word_to_Diphone[word_Index, diphone_Index] = self.parameter_Dict[("Feedback", "Word_to_Diphone_Activation")];
                else:
                    self.weightMatrix_Word_to_Diphone[word_Index, diphone_Index] = self.parameter_Dict[("Feedback", "Word_to_Diphone_Inhibition")];
            for single_Phone_Index in range(self.phoneme_Amount):
                if self.single_Phone_List[single_Phone_Index] in self.word_List[word_Index]:
                    self.weightMatrix_Word_to_Single_Phone[word_Index, single_Phone_Index] = self.parameter_Dict[("Feedback", "Word_to_SPhone_Activation")];
                else:
                    self.weightMatrix_Word_to_Single_Phone[word_Index, single_Phone_Index] = self.parameter_Dict[("Feedback", "Word_to_SPhone_Inhibition")];

        self.initialized = True;

    def Parameter_Display(self):
        if self.initialized:
            for key in self.parameter_Dict.keys():
                print(key[1] + "_" + key[0] + ": " + str(self.parameter_Dict[key]));
        else:
            print("Model is not initialized yet. PLEASE INITIALIZE BY USING 'Weight_Initialize()'");

    def Pattern_Generate(self, pronunciation, activation_Ratio_Dict = {}):
        if type(pronunciation) == str:
            inserted_Phoneme_List = [str(x) for x in pronunciation];
        elif type(pronunciation) == list:
            inserted_Phoneme_List = pronunciation;

        pattern = np.zeros(shape=(1, self.phoneme_Amount * self.parameter_Dict[("Length", "Time_Slot")]));

        for slot_Index in range(len(inserted_Phoneme_List)):
            if slot_Index in activation_Ratio_Dict.keys():
                for phoneme_Index in range(len(inserted_Phoneme_List[slot_Index])):
                    pattern[0, slot_Index * self.phoneme_Amount + self.phoneme_List.index(inserted_Phoneme_List[slot_Index][phoneme_Index])] = activation_Ratio_Dict[slot_Index][phoneme_Index];
            else:
                for phoneme in inserted_Phoneme_List[slot_Index]:
                    pattern[0, slot_Index * self.phoneme_Amount + self.phoneme_List.index(phoneme)] = 1 / float(len(inserted_Phoneme_List[slot_Index]));

        return pattern;

    def Open_Diphone_Generate(self, pronunciation):
        open_Diphone_List = [];

        for first_Index in range(len(pronunciation)):
            for second_Index in range(first_Index + 1, len(pronunciation)):
                if not pronunciation[first_Index] + pronunciation[second_Index] in open_Diphone_List:
                     open_Diphone_List.append(pronunciation[first_Index] + pronunciation[second_Index]); #Open Diphone

        return open_Diphone_List;

    def Run(self, pronunciation, activation_Ratio_Dict = {}):
        """
        Export the activation result about selected representations in inserted pronunciation simulation.

        Parameters
        ----------
        pronunciation : string or list of string
            The list or string about phonemes.

        activation_Ratio_Dict : dict, optional
            This dict decided the phoneme activation of specific location. If you do not set, model will assign '1/size'

        Returns
        -------
        out : ndarrays
            phoneme, diphone, single phone, and word activation matrix. Each matrix's first dimension is 'Time slot * ISetp'. This is cycle. You can see the specific timing by [row_Index,:]. Column index relates with the representation. You can know that each index represent what from the 'self.phoneme_List', 'self.diphone_List', 'self.diphone_List', and 'self_word_List'.

        """

        using_Pattern = self.Pattern_Generate(pronunciation, activation_Ratio_Dict);
        phoneme_Activation_Cycle_List = [];
        diphone_Activation_Cycle_List = [];
        single_Phone_Activation_Cycle_List = [];
        word_Activation_Cycle_List = [];

        ##Gate initialize
        gate_Phoneme_to_Diphone = np.zeros(shape=(self.phoneme_Amount*self.parameter_Dict[("Length", "Time_Slot")], self.diphone_Amount)) + 1; #Initially all gates have state 1

        ##Layer Initialize
        phoneme_Layer_Activation = np.zeros(shape = (1, self.phoneme_Amount * self.parameter_Dict[("Length", "Time_Slot")]))
        diphone_Layer_Activation = np.zeros(shape = (1, self.diphone_Amount));
        single_Phone_Layer_Activation = np.zeros(shape = (1, self.phoneme_Amount));
        word_Layer_Activation = np.zeros(shape = (1, self.word_Amount));

        for slot_Index in range(self.parameter_Dict[("Length", "Time_Slot")]):
            location_Input = np.zeros(shape = (1, self.phoneme_Amount * self.parameter_Dict[("Length", "Time_Slot")]));
            location_Input[0, slot_Index*self.phoneme_Amount:(slot_Index+1)*self.phoneme_Amount] = 1;
            #Time control (The current phoneme location of pronunication)
            for step_Index in range(self.parameter_Dict[("Length", "IStep")]):
                phoneme_Layer_Stroage = (using_Pattern * location_Input) * self.parameter_Dict[("Weight", "Input_to_Phoneme")];
                diphone_Layer_Stroage = phoneme_Layer_Activation.dot(gate_Phoneme_to_Diphone * self.weightMatrix_Phoneme_to_Diphone)
                diphone_Layer_Stroage = np.sign((np.sign(diphone_Layer_Stroage - self.parameter_Dict[("Length", "Threshold")]) + 1) /2) / 10 + word_Layer_Activation.dot(self.weightMatrix_Word_to_Diphone);  #Binary + Feedback
                single_Phone_Layer_Stroage = phoneme_Layer_Activation.dot(self.weightMatrix_Phoneme_to_Single_Phone);
                single_Phone_Layer_Stroage = np.sign((np.sign(single_Phone_Layer_Stroage - self.parameter_Dict[("Length", "Threshold")]) + 1) /2) / 10 + word_Layer_Activation.dot(self.weightMatrix_Word_to_Single_Phone);  #Binary + Feedback
                word_Layer_Stroage = diphone_Layer_Activation.dot(self.weightMatrix_Diphone_to_Word) + single_Phone_Layer_Activation.dot(self.weightMatrix_Single_Phone_to_Word) + word_Layer_Activation.dot(self.weightMatrix_Word_to_Word);

                phoneme_Layer_Activation = np.clip(phoneme_Layer_Activation * (1 - self.parameter_Dict[("Decay", "Phoneme")]) - np.abs(phoneme_Layer_Stroage) * phoneme_Layer_Activation + phoneme_Layer_Stroage.clip(min=0), 0, 1);
                diphone_Layer_Activation = np.clip(diphone_Layer_Activation * (1 - self.parameter_Dict[("Decay", "Diphone")]) - np.abs(diphone_Layer_Stroage) * diphone_Layer_Activation + diphone_Layer_Stroage.clip(min=0), 0, 1);
                single_Phone_Layer_Activation = np.clip(single_Phone_Layer_Activation * (1 - self.parameter_Dict[("Decay", "SPhone")]) - np.abs(single_Phone_Layer_Stroage) * single_Phone_Layer_Activation + single_Phone_Layer_Stroage.clip(min=0), 0, 1);
                word_Layer_Activation = np.clip(word_Layer_Activation * (1 - self.parameter_Dict[("Decay", "Word")]) - np.abs(word_Layer_Stroage) * word_Layer_Activation + word_Layer_Stroage.clip(min=0), 0, 1);

                phoneme_Activation_Cycle_List.append(phoneme_Layer_Activation.ravel());
                diphone_Activation_Cycle_List.append(diphone_Layer_Activation.ravel());
                single_Phone_Activation_Cycle_List.append(single_Phone_Layer_Activation.ravel());
                word_Activation_Cycle_List.append(word_Layer_Activation.ravel());
            #Gate Close
            if slot_Index < len(pronunciation): #If slot_Index is same or bigger than length of pronunciation, there is no input
                for diphone_Index in range(self.diphone_Amount):
                    if pronunciation[slot_Index] == self.diphone_List[diphone_Index][0] and pronunciation[slot_Index] != self.diphone_List[diphone_Index][1]: #Forward phone is same to inserted, and bacward phone is different
                        for slot_Index_for_Gate in range(slot_Index + 1, self.parameter_Dict[("Length", "Time_Slot")]):   #This mean closing process only affect the slots which are after current slot.
                            gate_Phoneme_to_Diphone[slot_Index_for_Gate * self.phoneme_Amount + self.phoneme_List.index(pronunciation[slot_Index]),diphone_Index] = 0;    #Assign 0

        return np.array(phoneme_Activation_Cycle_List), np.array(diphone_Activation_Cycle_List), np.array(single_Phone_Activation_Cycle_List), np.array(word_Activation_Cycle_List);

    def RT_Absolute_Threshold(self, pronunciation, word_Activation_Array, criterion = 0.75):
        target_Index = self.word_List.index(pronunciation);
        target_Array = word_Activation_Array[:,target_Index]
        other_Max_Array = np.max(np.delete(word_Activation_Array, (target_Index), 1), axis=1);
        check_Array = (target_Array > criterion) * (other_Max_Array < criterion);

        for cycle in range(self.parameter_Dict[("Length", "Time_Slot")] * self.parameter_Dict[("Length", "IStep")]):
            if check_Array[cycle]:
                return cycle;

        return np.nan;

    def RT_Relative_Threshold(self, pronunciation, word_Activation_Array, criterion = 0.05):
        target_Index = self.word_List.index(pronunciation);
        target_Array = word_Activation_Array[:,target_Index]
        other_Max_Array = np.max(np.delete(word_Activation_Array, (target_Index), 1), axis=1);

        for cycle in range(self.parameter_Dict[("Length", "Time_Slot")] * self.parameter_Dict[("Length", "IStep")]):
            if target_Array[cycle] > other_Max_Array[cycle] + criterion:
                return cycle;

        return np.nan;

    def RT_Time_Dependent(self, pronunciation, word_Activation_Array, criterion = 10):
        target_Index = self.word_List.index(pronunciation);
        target_Array = word_Activation_Array[:,target_Index]
        other_Max_Array = np.max(np.delete(word_Activation_Array, (target_Index), 1), axis=1);
        check_Array = target_Array > other_Max_Array;

        for cycle in range(self.parameter_Dict[("Length", "Time_Slot")] * self.parameter_Dict[("Length", "IStep")] - criterion):
            if all(check_Array[cycle:cycle+criterion]):
                return cycle + criterion;

        return np.nan;

    def Run_List(self, pronunciation_List, absolute_Acc_Criteria=0.75, relative_Acc_Criteria=0.05, time_Acc_Criteria=10, output_File_Name=None, raw_Data=False, categorize=False):
        """
        Export the raw data and categorized result about all pronunciations of inserted list.

        Parameters
        ----------
        pronunciation_List : list of string or string list
            The list or pronunciations. Each item should be a phoneme string of a list of phonemes.

        absolute_Acc_Criteria: float
            The criteria for the calculation of reaction time and accuracy. The value is for the absolute threshold.

        relative_Acc_Criteria: float
            The criteria for the calculation of reaction time and accuracy. The value is for the relative threshold.

        time_Acc_Criteria: integer
            The criteria for the calculation of reaction time and accuracy. The value is for the time-dependent criteria.

        output_File_Name: string, optional
            The prefix of export files.

        raw_Data : bool, optional
            The exporting of raw data. If this parameter is ‘True’, 4 files will be exported about the activation pattern of all units of all layers of all pronunciations of inserted list.

        categorize : bool, optional
            The exporting of categorized result. If this parameter is ‘True’, a file will be exported about the mean activation pattern of the target, cohort, rhyme, embedding words of all pronunciations of inserted list.

        Returns
        -------
        out : list of float
            the accuracy about inserted pronunciations

        """

        rt_Absolute_Threshold_List = [];
        rt_Relative_Threshold_List = [];
        rt_Time_Dependent_List = [];

        phoneme_Activation_Array_List = [];
        diphone_Activation_Array_List = [];
        single_Phone_Activation_Array_List = [];
        word_Activation_Array_List = [];
        for pronunciation in pronunciation_List:
            phoneme_Activation_Array, diphone_Activation_Array, single_Phone_Activation_Array, word_Activation_Array = self.Run(pronunciation);
            phoneme_Activation_Array_List.append(phoneme_Activation_Array);
            diphone_Activation_Array_List.append(diphone_Activation_Array);
            single_Phone_Activation_Array_List.append(single_Phone_Activation_Array);
            word_Activation_Array_List.append(word_Activation_Array);

            rt_Absolute_Threshold_List.append(self.RT_Absolute_Threshold(pronunciation, word_Activation_Array, absolute_Acc_Criteria));
            rt_Relative_Threshold_List.append(self.RT_Relative_Threshold(pronunciation, word_Activation_Array, relative_Acc_Criteria));
            rt_Time_Dependent_List.append(self.RT_Time_Dependent(pronunciation, word_Activation_Array, time_Acc_Criteria));

        if raw_Data:
            output_Phoneme_Activation_Data = ["Target\tPhoneme\tPosition\t" + "\t".join([str(x) for x in range(0,self.parameter_Dict[("Length", "Time_Slot")] * self.parameter_Dict[("Length", "IStep")])]) + "\n"];
            output_Diphone_Activation_Data = ["Target\tDiphone\t" + "\t".join([str(x) for x in range(0,self.parameter_Dict[("Length", "Time_Slot")] * self.parameter_Dict[("Length", "IStep")])]) + "\n"];
            output_Single_Phone_Activation_Data = ["Target\tSingle_Phone\t" + "\t".join([str(x) for x in range(0,self.parameter_Dict[("Length", "Time_Slot")] * self.parameter_Dict[("Length", "IStep")])]) + "\n"];
            output_Word_Activation_Data = ["Target\tWord\t" + "\t".join([str(x) for x in range(0,self.parameter_Dict[("Length", "Time_Slot")] * self.parameter_Dict[("Length", "IStep")])]) + "\n"];

            for pronunciation in sorted(pronunciation_List):
                pronunciation_Index = pronunciation_List.index(pronunciation);
                for phoneme in sorted(self.phoneme_List):
                    for location in range(self.parameter_Dict[("Length", "Time_Slot")]):
                        phoneme_Index = self.phoneme_Amount * location + self.phoneme_List.index(phoneme);
                        output_Phoneme_Activation_Data.append(pronunciation + "\t" + phoneme + "\t" + str(location) + "\t" + "\t".join([str(x) for x in phoneme_Activation_Array_List[pronunciation_Index][:,phoneme_Index]]) + "\n");

                for diphone in sorted(self.diphone_List):
                    diphone_Index = self.diphone_List.index(diphone);
                    output_Diphone_Activation_Data.append(pronunciation + "\t" + diphone + "\t" + "\t".join([str(x) for x in diphone_Activation_Array_List[pronunciation_Index][:,diphone_Index]]) + "\n");

                for single_Phone in sorted(self.single_Phone_List):
                    single_Phone_Index = self.single_Phone_List.index(single_Phone);
                    output_Single_Phone_Activation_Data.append(pronunciation + "\t" + single_Phone + "\t" + "\t".join([str(x) for x in single_Phone_Activation_Array_List[pronunciation_Index][:,single_Phone_Index]]) + "\n");

                for word in sorted(self.word_List):
                    word_Index = self.word_List.index(word);
                    output_Word_Activation_Data.append(pronunciation + "\t" + word + "\t" + "\t".join([str(x) for x in word_Activation_Array_List[pronunciation_Index][:,word_Index]]) + "\n");

            with open(output_File_Name + "_Phoneme_Activation_Data.txt", "w") as fileStream:
                fileStream.write("".join(output_Phoneme_Activation_Data));
            with open(output_File_Name + "_Diphone_Activation_Data.txt", "w") as fileStream:
                fileStream.write("".join(output_Diphone_Activation_Data));
            with open(output_File_Name + "_Single_Phone_Activation_Data.txt", "w") as fileStream:
                fileStream.write("".join(output_Single_Phone_Activation_Data));
            with open(output_File_Name + "_Word_Activation_Data.txt", "w") as fileStream:
                fileStream.write("".join(output_Word_Activation_Data));

        if categorize:
            output_Category_Activation_Average_Data = ["Target\tCategory\t" + "\t".join([str(x) for x in range(0,self.parameter_Dict[("Length", "Time_Slot")] * self.parameter_Dict[("Length", "IStep")])]) + "\n"];

            for pronunciation in sorted(pronunciation_List):
                pronunciation_Index = pronunciation_List.index(pronunciation);
                cohort_List, rhyme_List, embedding_List, other_List = self.Category_List(pronunciation)

                target_Activation_List = [];
                cohort_Activation_List = [];
                rhyme_Activation_List = [];
                embedding_Activation_List = [];
                other_Activation_List = [];

                for word in sorted(self.word_List):
                    word_Index = self.word_List.index(word);
                    if pronunciation == word:
                        target_Activation_List.append(word_Activation_Array_List[pronunciation_Index][:,word_Index]);
                    if word in cohort_List:
                        cohort_Activation_List.append(word_Activation_Array_List[pronunciation_Index][:,word_Index]);
                    if word in rhyme_List:
                        rhyme_Activation_List.append(word_Activation_Array_List[pronunciation_Index][:,word_Index]);
                    if word in embedding_List:
                        embedding_Activation_List.append(word_Activation_Array_List[pronunciation_Index][:,word_Index]);
                    if word in other_List:
                        other_Activation_List.append(word_Activation_Array_List[pronunciation_Index][:,word_Index]);

                if len(target_Activation_List) == 0:
                    target_Activation_List.append(np.zeros(self.parameter_Dict[("Length", "Time_Slot")] * self.parameter_Dict[("Length", "IStep")]));
                if len(cohort_Activation_List) == 0:
                    cohort_Activation_List.append(np.zeros(self.parameter_Dict[("Length", "Time_Slot")] * self.parameter_Dict[("Length", "IStep")]));
                if len(rhyme_Activation_List) == 0:
                    rhyme_Activation_List.append(np.zeros(self.parameter_Dict[("Length", "Time_Slot")] * self.parameter_Dict[("Length", "IStep")]));
                if len(embedding_Activation_List) == 0:
                    embedding_Activation_List.append(np.zeros(self.parameter_Dict[("Length", "Time_Slot")] * self.parameter_Dict[("Length", "IStep")]));
                if len(other_Activation_List) == 0:
                    other_Activation_List.append(np.zeros(self.parameter_Dict[("Length", "Time_Slot")] * self.parameter_Dict[("Length", "IStep")]));

                output_Category_Activation_Average_Data.append(pronunciation + "\tTarget\t" + "\t".join([str(x) for x in np.mean(target_Activation_List, axis=0)]) + "\n");
                output_Category_Activation_Average_Data.append(pronunciation + "\tCohort\t" + "\t".join([str(x) for x in np.mean(cohort_Activation_List, axis=0)]) + "\n");
                output_Category_Activation_Average_Data.append(pronunciation + "\tRhyme\t" + "\t".join([str(x) for x in np.mean(rhyme_Activation_List, axis=0)]) + "\n");
                output_Category_Activation_Average_Data.append(pronunciation + "\tEmbedding\t" + "\t".join([str(x) for x in np.mean(embedding_Activation_List, axis=0)]) + "\n");
                output_Category_Activation_Average_Data.append(pronunciation + "\tOther\t" + "\t".join([str(x) for x in np.mean(other_Activation_List, axis=0)]) + "\n");

            with open(output_File_Name + "_Category_Activation_Data.txt", "w") as fileStream:
                fileStream.write("".join(output_Category_Activation_Average_Data));

        result_List = [];
        result_List.append(np.nanmean(rt_Absolute_Threshold_List))
        result_List.append(np.count_nonzero(~np.isnan(rt_Absolute_Threshold_List)) / len(pronunciation_List))
        result_List.append(np.nanmean(rt_Relative_Threshold_List))
        result_List.append(np.count_nonzero(~np.isnan(rt_Relative_Threshold_List)) / len(pronunciation_List))
        result_List.append(np.nanmean(rt_Time_Dependent_List))
        result_List.append(np.count_nonzero(~np.isnan(rt_Time_Dependent_List)) / len(pronunciation_List))

        return result_List;

    def Category_List(self, pronunciation):
        cohort_List = [];
        rhyme_List = [];
        embedding_List = [];
        other_List = [];

        for word in self.word_List:
            if pronunciation == word:
                continue;
            if pronunciation[0:2] == word[0:2]:
                cohort_List.append(word);
            if pronunciation[1:] == word[1:] and pronunciation[0] != word[0]:
                rhyme_List.append(word);
            if word in pronunciation:
                embedding_List.append(word);
            if pronunciation != word and not word in cohort_List and not word in rhyme_List and not word in embedding_List:
                other_List.append(word);

        return cohort_List, rhyme_List, embedding_List, other_List;

    def Display_Graph(self, pronunciation, activation_Ratio_Dict = {}, display_Phoneme_List = None, display_Diphone_List = None, display_Single_Phone_List = None, display_Word_List = None, file_Save = False):
        """
        Export the graphs about selected representations in inserted pronunciation simulation.

        Parameters
        ----------
        pronunciation : string or list of string
            The list or string about phonemes.

        activation_Ratio_Dict : dict, optional
            This dict decided the phoneme activation of specific location. If you do not set, model will assign '1/size'

        display_Phoneme_List : list of tuple, optional
            The list which what phonemes are displayed in the exported phoneme graph. An item of this list should be a tuple which the shape is '(phoeme, location)'.

        display_Diphone_List : list of string, optional
            The list which what diphones are displayed in the exported diphone graph. An item of this list should be a diphone string.

        display_Single_Phone_List : list of string, optional
            The list which what single phones are displayed in the exported single phone graph. An item of this list should be a single phone character.

        display_Word_List : list of string, optional
            The list which what words are displayed in the exported word graph. An item of this list should be a word string.

        """


        marker_list = [",", "o", "v", "^", "<", ">", "1", "2", "3", "4", "s", "p", "*", "h", "H", "+", "x", "D", "d", "|", "_"];

        phoneme_Activation_Array, diphone_Activation_Array, single_Phone_Activation_Array, word_Activation_Array = self.Run(pronunciation, activation_Ratio_Dict);

        if not display_Phoneme_List is None:
            activation_List = [];
            for display_Phoneme in display_Phoneme_List:
                phoneme_Index = self.phoneme_List.index(display_Phoneme[0]) + (display_Phoneme[1] * len(self.phoneme_List));
                activation_List.append(phoneme_Activation_Array[:,phoneme_Index]);

            display_Data = np.zeros(shape=(len(activation_List), self.parameter_Dict[("Length", "Time_Slot")] * self.parameter_Dict[("Length", "IStep")]));
            for index in range(len(activation_List)):
                display_Data[index] = activation_List[index];

            fig = plt.figure(figsize=(8, 8));
            for y_arr, label, marker in zip(display_Data, display_Phoneme_List, marker_list[0:len(display_Phoneme_List)]):
                plt.plot(list(range(self.parameter_Dict[("Length", "Time_Slot")] * self.parameter_Dict[("Length", "IStep")])), y_arr, label=label, marker=marker);

            plt.title("Phoneme (Inserted: " + " ".join(pronunciation) + ")");
            plt.gca().set_xlim([0, self.parameter_Dict[("Length", "Time_Slot")] * self.parameter_Dict[("Length", "IStep")]])
            plt.gca().set_ylim([-0.01,1.01])
            plt.legend();
            plt.draw();
            if file_Save:
                plt.savefig(" ".join(pronunciation) + "_Phoneme.png");

        if not display_Diphone_List is None:
            activation_List = [];
            for display_Diphone in display_Diphone_List:
                diphone_Index = self.diphone_List.index(display_Diphone);
                activation_List.append(diphone_Activation_Array[:,diphone_Index]);

            display_Data = np.zeros(shape=(len(activation_List), self.parameter_Dict[("Length", "Time_Slot")] * self.parameter_Dict[("Length", "IStep")]));
            for index in range(len(activation_List)):
                display_Data[index] = activation_List[index];

            fig = plt.figure(figsize=(8, 8));
            for y_arr, label, marker in zip(display_Data, display_Diphone_List, marker_list[0:len(display_Diphone_List)]):
                plt.plot(list(range(self.parameter_Dict[("Length", "Time_Slot")] * self.parameter_Dict[("Length", "IStep")])), y_arr, label=label, marker=marker);

            plt.title("Diphone (Inserted: " + " ".join(pronunciation) + ")");
            plt.gca().set_xlim([0, self.parameter_Dict[("Length", "Time_Slot")] * self.parameter_Dict[("Length", "IStep")]])
            plt.gca().set_ylim([-0.01,1.01])
            plt.legend();
            plt.draw();
            if file_Save:
                plt.savefig(" ".join(pronunciation) + "_Diphone.png");

        if not display_Single_Phone_List is None:
            activation_List = [];
            for display_Single_Phone in display_Single_Phone_List:
                single_Phone_Index = self.single_Phone_List.index(display_Single_Phone);
                activation_List.append(single_Phone_Activation_Array[:,single_Phone_Index]);

            display_Data = np.zeros(shape=(len(activation_List), self.parameter_Dict[("Length", "Time_Slot")] * self.parameter_Dict[("Length", "IStep")]));
            for index in range(len(activation_List)):
                display_Data[index] = activation_List[index];

            fig = plt.figure(figsize=(8, 8));
            for y_arr, label, marker in zip(display_Data, display_Single_Phone_List, marker_list[0:len(display_Single_Phone_List)]):
                plt.plot(list(range(self.parameter_Dict[("Length", "Time_Slot")] * self.parameter_Dict[("Length", "IStep")])), y_arr, label=label, marker=marker);

            plt.title("Single Phone (Inserted: " + " ".join(pronunciation) + ")");
            plt.gca().set_xlim([0, self.parameter_Dict[("Length", "Time_Slot")] * self.parameter_Dict[("Length", "IStep")]])
            plt.gca().set_ylim([-0.01,1.01])
            plt.legend();
            plt.draw();
            if file_Save:
                plt.savefig(" ".join(pronunciation) + "_Single_Phone.png");

        if not display_Word_List is None:
            activation_List = [];
            for display_Word in display_Word_List:
                word_Index = self.word_List.index(display_Word);
                activation_List.append(word_Activation_Array[:,word_Index]);

            display_Data = np.zeros(shape=(len(activation_List), self.parameter_Dict[("Length", "Time_Slot")] * self.parameter_Dict[("Length", "IStep")]));
            for index in range(len(activation_List)):
                display_Data[index] = activation_List[index];

            fig = plt.figure(figsize=(8, 8));
            for y_arr, label, marker in zip(display_Data, display_Word_List, marker_list[0:len(display_Word_List)]):
                plt.plot(list(range(self.parameter_Dict[("Length", "Time_Slot")] * self.parameter_Dict[("Length", "IStep")])), y_arr, label=label, marker=marker);

            plt.title("Word (Inserted: " + " ".join(pronunciation) + ")");
            plt.gca().set_xlim([0, self.parameter_Dict[("Length", "Time_Slot")] * self.parameter_Dict[("Length", "IStep")]])
            plt.gca().set_ylim([-0.01,1.01])
            plt.legend();
            plt.draw();
            if file_Save:
                plt.savefig(" ".join(pronunciation) + "_Word.png");

        plt.show(block=False);

    def Extract_Data(self, pronunciation, activation_Ratio_Dict = {}, extract_Phoneme_List = None, extract_Diphone_List = None, extract_Single_Phone_List = None, extract_Word_List = None, file_Save = False):
        """
        Export the activation result about selected representations in inserted pronunciation simulation.

        Parameters
        ----------
        pronunciation : string or list of string
            The list or string about phonemes.

        activation_Ratio_Dict : dict, optional
            This dict decided the phoneme activation of specific location. If you do not set, model will assign '1/size'

        display_Phoneme_List : list of tuple, optional
            The list which what phonemes are displayed in the exported phoneme graph. An item of this list should be a tuple which the shape is '(phoeme, location)'.

        display_Diphone_List : list of string, optional
            The list which what diphones are displayed in the exported diphone graph. An item of this list should be a diphone string.

        display_Single_Phone_List : list of string, optional
            The list which what single phones are displayed in the exported single phone graph. An item of this list should be a single phone character.

        display_Word_List : list of string, optional
            The list which what words are displayed in the exported word graph. An item of this list should be a word string.

        file_Save: bool, optional
            If this parameter is 'True', the activation pattern of the representations which you select will be exported.

        Returns
        -------
        out : list of ndarray
            the list parameters are not None value, the activation pattern of the list is in the array. For example, if 'display_Phoneme_List' and 'display_Single_Phone_List' are not None, the returned array's first and second indexs are the result of phoneme and single phoneme, respectively. The order is 'phoneme, diphone, single phone, and word'.

        """

        phoneme_Activation_Array, diphone_Activation_Array, single_Phone_Activation_Array, word_Activation_Array = self.Run(pronunciation, activation_Ratio_Dict);

        result_Array = [];

        if not extract_Phoneme_List is None:
            activation_List = [];
            for extract_Phoneme in extract_Phoneme_List:
                phoneme_Index = self.phoneme_List.index(extract_Phoneme[0]) + (extract_Phoneme[1] * len(self.phoneme_List));
                activation_List.append(phoneme_Activation_Array[:,phoneme_Index]);
            result_Array.append(np.vstack(activation_List));

            if file_Save:
                with open(" ".join(pronunciation) + "_Phoneme.txt", "w") as f:
                    extract_Text = ["Target\tPhoneme\t" + "\t".join([str(x) for x in range(0,self.parameter_Dict[("Length", "Time_Slot")] * self.parameter_Dict[("Length", "IStep")])]) + "\n"];
                    for index in range(len(extract_Phoneme_List)):
                        extract_Text.append(" ".join(pronunciation) + "\t" + str(extract_Phoneme_List[index]) + "\t");
                        extract_Text.append("\t".join([str(x) for x in activation_List[index]]));
                        extract_Text.append("\n");
                    f.write("".join(extract_Text));

        if not extract_Diphone_List is None:
            activation_List = [];
            for extract_Diphone in extract_Diphone_List:
                diphone_Index = self.diphone_List.index(extract_Diphone);
                activation_List.append(diphone_Activation_Array[:,diphone_Index]);
            result_Array.append(np.vstack(activation_List));

            if file_Save:
                with open(" ".join(pronunciation) + "_Diphone.txt", "w") as f:
                    extract_Text = ["Target\tDiphone\t" + "\t".join([str(x) for x in range(0,self.parameter_Dict[("Length", "Time_Slot")] * self.parameter_Dict[("Length", "IStep")])]) + "\n"];
                    for index in range(len(extract_Diphone_List)):
                        extract_Text.append(" ".join(pronunciation) + "\t" + str(extract_Diphone_List[index]) + "\t");
                        extract_Text.append("\t".join([str(x) for x in activation_List[index]]));
                        extract_Text.append("\n");
                    f.write("".join(extract_Text));

        if not extract_Single_Phone_List is None:
            activation_List = [];
            for extract_Single_Phone in extract_Single_Phone_List:
                single_Phone_Index = self.single_Phone_List.index(extract_Single_Phone);
                activation_List.append(single_Phone_Activation_Array[:,single_Phone_Index]);
            result_Array.append(np.vstack(activation_List));

            if file_Save:
                with open(" ".join(pronunciation) + "_Single_Phone.txt", "w") as f:
                    extract_Text = ["Target\tSingle_Phone\t" + "\t".join([str(x) for x in range(0,self.parameter_Dict[("Length", "Time_Slot")] * self.parameter_Dict[("Length", "IStep")])]) + "\n"];
                    for index in range(len(extract_Single_Phone_List)):
                        extract_Text.append(" ".join(pronunciation) + "\t" + str(extract_Single_Phone_List[index]) + "\t");
                        extract_Text.append("\t".join([str(x) for x in activation_List[index]]));
                        extract_Text.append("\n");
                    f.write("".join(extract_Text));

        if not extract_Word_List is None:
            activation_List = [];
            for extract_Word in extract_Word_List:
                word_Index = self.word_List.index(extract_Word);
                activation_List.append(word_Activation_Array[:,word_Index]);
            result_Array.append(np.vstack(activation_List));

            if file_Save:
                with open(" ".join(pronunciation) + "_Word.txt", "w") as f:
                    extract_Text = ["Target\tWord\t" + "\t".join([str(x) for x in range(0,self.parameter_Dict[("Length", "Time_Slot")] * self.parameter_Dict[("Length", "IStep")])]) + "\n"];
                    for index in range(len(extract_Word_List)):
                        extract_Text.append(" ".join(pronunciation) + "\t" + str(extract_Word_List[index]) + "\t");
                        extract_Text.append("\t".join([str(x) for x in activation_List[index]]));
                        extract_Text.append("\n");
                    f.write("".join(extract_Text));

        return result_Array;

    def Average_Activation_by_Category_Graph(self, pronunciation_List, file_Save = False):
        marker_list = [",", "o", "v", "^", "<", ">", "1", "2", "3", "4", "s", "p", "*", "h", "H", "+", "x", "D", "d", "|", "_"];

        target_Activation_List = [];
        cohort_Activation_List = [];
        rhyme_Activation_List = [];
        embedding_Activation_List = [];
        other_Activation_List = [];

        for pronunciation in pronunciation_List:
            cohort_List, rhyme_List, embedding_List, other_List = self.Category_List(pronunciation);
            target_Activation_List.append(self.Extract_Data(pronunciation, extract_Word_List=[pronunciation])[0]);
            if len(cohort_List) > 0:
                cohort_Activation_List.append(self.Extract_Data(pronunciation, extract_Word_List=cohort_List)[0]);
            if len(rhyme_List) > 0:
                rhyme_Activation_List.append(self.Extract_Data(pronunciation, extract_Word_List=rhyme_List)[0]);
            if len(embedding_List) > 0:
                embedding_Activation_List.append(self.Extract_Data(pronunciation, extract_Word_List=embedding_List)[0]);
            if len(other_List) > 0:
                other_Activation_List.append(self.Extract_Data(pronunciation, extract_Word_List=other_List)[0]);

        display_Data_List = [];
        display_Category_List = [];

        if len(target_Activation_List) > 0:
            display_Data_List.append(np.mean(np.vstack(target_Activation_List), axis=0));
            display_Category_List.append("Target");

        if len(cohort_Activation_List) > 0:
            display_Data_List.append(np.mean(np.vstack(cohort_Activation_List), axis=0));
            display_Category_List.append("Cohort");

        if len(rhyme_Activation_List) > 0:
            display_Data_List.append(np.mean(np.vstack(rhyme_Activation_List), axis=0));
            display_Category_List.append("Rhyme");

        if len(embedding_Activation_List) > 0:
            display_Data_List.append(np.mean(np.vstack(embedding_Activation_List), axis=0));
            display_Category_List.append("Embedding");

        if len(other_Activation_List) > 0:
            display_Data_List.append(np.mean(np.vstack(other_Activation_List), axis=0));
            display_Category_List.append("Other");

        fig = plt.figure(figsize=(8, 8));
        for y_arr, label, marker in zip(display_Data_List, display_Category_List, marker_list[0:len(display_Category_List)]):
            plt.plot(list(range(self.parameter_Dict[("Length", "Time_Slot")] * self.parameter_Dict[("Length", "IStep")])), y_arr, label=label, marker=marker);

        plt.title("Average activation by category");
        plt.gca().set_xlim([0, self.parameter_Dict[("Length", "Time_Slot")] * self.parameter_Dict[("Length", "IStep")]])
        plt.gca().set_ylim([-0.01,1.01])
        plt.legend();
        plt.draw();
        if file_Save:
            plt.savefig("Average_Activation_by_Category_Graph.png");

        plt.show(block=False);


if __name__ == "__main__":
    # Example
    phoneme_List, word_List = List_Generate();
    tisk_Model = TISK_Model(phoneme_List, word_List, time_Slot=10);

    # tisk_Model.Decay_Parameter_Assign(decay_Phoneme = 0.001, decay_Diphone = 0.1, decay_SPhone = 0.1, decay_Word = 0.05);
    # tisk_Model.Weight_Parameter_Assign(input_to_Phoneme_Weight = 1.0, phoneme_to_Phone_Weight = 0.1, diphone_to_Word_Weight = 0.05, sPhone_to_Word_Weight = 0.01, word_to_Word_Weight = -0.01);
    # tisk_Model.Feedback_Parameter_Assign(word_to_Diphone_Activation = 0.15, word_to_SPhone_Activation = 0.15, word_to_Diphone_Inhibition = -0.05, word_to_SPhone_Inhibition = -0.05);

    tisk_Model.Weight_Initialize();
    tisk_Model.Parameter_Display();
    # tisk_Model.Display_Graph(pronunciation="pat", display_Phoneme_List = [("p", 0), ("a",1), ("t", 2)], display_Diphone_List = ["pa", "pt", "ap"], display_Single_Phone_List = ["p", "a", "t"], display_Word_List = ["pat", "tap"]);
    # tisk_Model.Display_Graph(pronunciation="tap", display_Phoneme_List = [("t", 0), ("a",1), ("p", 2)], display_Diphone_List = ["pa", "pt", "at", "ta", "tp", "ap"], display_Single_Phone_List = ["p", "a", "t"], display_Word_List = ["pat", "tap"]);
    #print(tisk_Model.Run_List(word_List));

    #result = tisk_Model.Run(pronunciation='pat');
    #rt_and_ACC = tisk_Model.Run_List(pronunciation_List = ['baks', 'bar', 'bark', 'bat^l', 'bi'], categorize=True)

    # result = tisk_Model.Extract_Data(pronunciation='pat',
    #      extract_Phoneme_List = [("p", 0), ("a",1), ("t", 2)], extract_Diphone_List = ["pa", "pt", "ap"], extract_Single_Phone_List = ["p", "a", "t"],
    #      extract_Word_List = ['pat', 'tap'], file_Save=True)

    tisk_Model.Average_Activation_by_Category_Graph(word_List);
    input("Press Enter to continue...")
