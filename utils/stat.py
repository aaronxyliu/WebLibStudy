import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import math
from utils.standard_version import StandardVersion as SV

# Frequency
class Distribution:
    def __init__(self) -> None:
        self.dict = {}  # Store item and its frequency pair
        
    def add(self, item, value: str = ''):
        # item_str = str(item)
        if item not in self.dict:
            self.dict[item] = [value]
        else:
            self.dict[item].append(value)
    
    def add_distinct(self, item, value):
        if item not in self.dict:
            self.dict[item] = [value]
        else:
            if value not in self.dict[item]:
                self.dict[item].append(value)

    def size(self):
        # The sum of frequency
        size = 0
        for entry in self.dict.items():
            size += len(entry[1])
        return size
        
    def freqDict(self, title: str = None) -> str:
        # Frequency Distribution
        frequency_dict = {}
        for pair in self.dict.items():
            frequency_dict[pair[0]] = len(pair[1])

        # Sort by frequency from high to low
        frequency_dict = dict(sorted(frequency_dict.items(), key=lambda x:x[1], reverse=True))
        if title:
            return f"[== {str(title)} ==]\n" + str(frequency_dict)
        else:
            return frequency_dict
    
    def avgDateDict(self, title: str = None) -> str:
        # Average Date Distribution
        average_dict = {}
        for entry in self.dict.items():
            average_dict[entry[0]] = self.avgDate(entry[1])
        average_dict = dict(sorted(average_dict.items(), key=lambda d: int(''.join(d[1].split('-'))), reverse=True))
        # average_dict = dict(sorted(average_dict.items(), key=lambda d: d[0], reverse=False))

        if title:
            return f"[== {str(title)} ==]\n" + str(average_dict)
        else:
            return average_dict
    
    def avgDate(self, dates: list) -> str:
        # Calculate the average date for a list of dates
        if not dates or len(dates) == 0:
            return ''
        mean_date = (np.array(dates, dtype='datetime64[s]')
                            .view('i8')
                            .mean()
                            .astype('datetime64[s]'))
        return str(mean_date)[:10]

    def avgYear(self, dates: list) -> str:
        # Calculate the average date for a list of dates
        if not dates or len(dates) == 0:
            return ''
        mean_date = (np.array(dates, dtype='datetime64[s]')
                            .view('i8')
                            .mean()
                            .astype('datetime64[s]'))
        return str(mean_date)[:4]

    def mean(self, processFunc = len, isDate = False) -> float:
        if len(self.dict) == 0:
            return 0
        values = []
        for pair in self.dict.items():
            values.append(processFunc(pair[1]))
        # Calculate the mean for a list of values
        if isDate:
            return self.avgDate(values)
        else:
            return np.mean(values)
    
    def variance(self, processFunc = len, isDate = False) -> float:
        if len(self.dict) == 0:
            return 0
        values = []
        for pair in self.dict.items():
            values.append(processFunc(pair[1]))
        # Calculate the variance for a list of values
        if isDate:
            return np.array(values, dtype='datetime64[s]').view('i8').var()
        else:
            return np.var(values)
    
    def showplot(self, title: str = None, processFunc = len, xlabel: str = None, ylabel: str = None, sortByX: bool = False, sortByY: bool = False, head: int = -1, partition: int = -1, xrange: list=None, yrange: list=None, dateY:bool = False, strX:bool = False, verX:bool = False, hist:bool = False, thresY: float = -1):
        # "processFunc' must be a function that receives a list and returns a number
        # 'head' specify only display several items in the front
        # 'partition' makes data grouped by the X label
        if len(self.dict) == 0:
            return
        show_dict = self.dict.copy()
        if partition > 0:
            sortByX = True

        if sortByX:
            if verX:
                show_dict = dict(sorted(show_dict.items(), key=lambda x:SV(x), reverse=False))
            elif strX:
                show_dict = dict(sorted(show_dict.items(), key=lambda x:x[0], reverse=False))
            else:
                show_dict = dict(sorted(show_dict.items(), key=lambda x:float(x[0]), reverse=False))
        

        if partition > 0:
            # Group into partitiions after sorting by X label
            new_show_dict = {}
            i = 0
            for pair in show_dict.items():
                part_base = math.floor(i * partition / len(show_dict))
                part_start_index = math.floor(part_base * len(show_dict) / partition)
                part_end_index = math.floor((part_base + 1) * len(show_dict) / partition) - 1
                part_label = f'{list(show_dict)[part_start_index]} ~ {list(show_dict)[part_end_index]}'
                if part_label not in new_show_dict:
                    new_show_dict[part_label] = pair[1]
                else:
                    new_show_dict[part_label] += pair[1]
                i += 1
            show_dict = new_show_dict

        

        for pair in show_dict.items():
            # Calculate the frequency by default
            show_dict[pair[0]] = processFunc(pair[1])        

        # Sort by X or Y
        if sortByY:
            if dateY:
                show_dict = dict(sorted(show_dict.items(), key=lambda d: int(''.join(d[1].split('-'))), reverse=True))
            else:
                show_dict = dict(sorted(show_dict.items(), key=lambda x:x[1], reverse=True))
        

        x_list = []
        y_list = []
        
        i = 0
        for pair in show_dict.items():
            if head > 0 and i >= head:
                break
            if thresY > 0 and pair[1] <= thresY:
                # Filter out the data below the threshold
                continue
            x_item = pair[0]

            # The version title of core-js is too long
            # if x_item[0] == 'c':
            #     x_item = x_item[13:]
            
            x_list.append(x_item)
            y_list.append(pair[1])
            i += 1
        # print(y_list)
        
        if dateY:
            y_list = mdates.datestr2num(y_list)

        fig, ax = plt.subplots(figsize=(6.2, 3))

        if hist:
            plt.hist(y_list, bins=10, color="#F5CCCC", edgecolor="#C66667")
            if dateY:
                ax.xaxis_date()
        else:
            plt.bar(x=range(len(x_list)), height=y_list, width=0.9,
                color="#F5CCCC",
                edgecolor="#C66667")
            plt.xticks(range(len(x_list)), x_list)

        plt.xlabel(xlabel or "Item")
        plt.ylabel(ylabel or "Frequency")

        plt.xticks(rotation=-90)

        if yrange:
            if dateY:
                plt.ylim(bottom=mdates.datestr2num(yrange[0]), top=mdates.datestr2num(yrange[1]))
            else:
                plt.ylim(bottom=yrange[0], top=yrange[1])

        if dateY and not hist:
            ax.yaxis_date()

        if title:
            plt.title(title)
        plt.show()

    def showsbplot(self, title: str = None, processFunc = None, xlabel: str = None, ylabel: str = None, sortByY: bool = False, head: int = -1):
        # stacked bar plot
        # "processFunc' must be a function that receives a list and returns a dict

        item_len = len(self.dict)
        if item_len == 0:
            return
        
        fig, ax = plt.subplots()
        bottom = np.zeros(item_len)
        width = 0.4

        x_list = []
        
        stack_dicts = []
        for pair in self.dict.items():
            x_list.append(pair[0])
            stack_dicts.append(processFunc(pair[1]))

        for k, _ in stack_dicts[0]:
            weights = np.array()
            for stack_dict in stack_dicts:
                weights = np.append(weights, stack_dict[k])
            ax.bar(x_list, weights, width, label=str(k), bottom=bottom) 
            bottom += weights

        
        ax.set_title("Number of penguins with above average body mass")
        ax.legend(loc="upper right")

        plt.show()


class Scatter:
    def __init__(self, xlist, ylist) -> None:
        self.xlist = xlist
        self.ylist = ylist

    def plot(self, title: str = None, xlabel: str = None, ylabel: str = None, dateY: bool = False, yrange: list=None):
        fig, ax = plt.subplots()
        plt.scatter(self.xlist, self.ylist)
        plt.xlabel(xlabel or "x")
        plt.ylabel(ylabel or "y")
        if yrange:
            if dateY:
                plt.ylim(bottom=mdates.datestr2num(yrange[0]), top=mdates.datestr2num(yrange[1]))
            else:
                plt.ylim(bottom=yrange[0], top=yrange[1])
        if dateY:
            ax.yaxis_date()
        if title:
            plt.title(title)
        plt.show()


            