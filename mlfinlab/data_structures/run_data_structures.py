"""
Advances in Financial Machine Learning, Marcos Lopez de Prado
Chapter 2: Financial Data Structures

This module contains the functions to help users create structured financial data from raw unstructured data,
in the form of tick, volume, and dollar run bars.

These bars are used throughout the text book (Advances in Financial Machine Learning, By Marcos Lopez de Prado, 2018,
pg 31) to build the more interesting features for predicting financial time series data.

These financial data structures have better statistical properties when compared to those based on fixed time interval
sampling. A great paper to read more about this is titled: The Volume Clock: Insights into the high frequency paradigm,
Lopez de Prado, et al. These ideas are then extended in another paper: Flow toxicity and liquidity
in a high-frequency world.


A good blog post to read, which helped us a lot in the implementation here is writen by Maksim Ivanov:
https://towardsdatascience.com/financial-machine-learning-part-0-bars-745897d4e4ba
"""

# Imports
import numpy as np
import pandas as pd

from mlfinlab.util.fast_ewma import ewma
from mlfinlab.data_structures.base_bars import BaseRunBars


class EMARunBars(BaseRunBars):
    """
    Contains all of the logic to construct the run bars from chapter 2. This class shouldn't be used directly.
    We have added functions to the package such as get_ema_dollar_imbalance_bars which will create an instance of this
    class and then construct the run bars, to return to the user.

    This is because we wanted to simplify the logic as much as possible, for the end user.
    """

    def __init__(self, file_path_or_df, metric, num_prev_bars, expected_imbalance_window, exp_num_ticks_init,
                 exp_num_ticks_constraints, batch_size, analyse_thresholds):
        """
        Constructor

        :param file_path_or_df: (String) Path to the csv file or Pandas Data Frame containing raw tick data in the format[date_time, price, volume]
        :param metric: (String) type of run bar to create. Example: "dollar_run"
        :param num_prev_bars: (Int) Window size for E[T]s (number of previous bars to use for expected number of ticks estimation)
        :param expected_imbalance_window: (Int) EMA window used to estimate expected imbalance
        :param exp_num_ticks_init: (Int) Initial number of expected ticks
        :param exp_num_ticks_constraints (Array) Minimum and maximum possible number of expected ticks. Used to control bars sampling convergence
        :param batch_size: (Int) Number of rows to read in from the csv, per batch
        :param analyse_thresholds: (Bool) flag to return thresholds values (theta, exp_num_ticks, exp_imbalance) in a
                                          form of Pandas DataFrame
        """
        BaseRunBars.__init__(self, file_path_or_df, metric, batch_size, num_prev_bars, expected_imbalance_window,
                             exp_num_ticks_init,
                             analyse_thresholds)

        # EMA Run Bars specific hyper parameters
        if exp_num_ticks_constraints is None:
            self.min_exp_num_ticks = 0
            self.max_exp_num_ticks = np.inf
        else:
            self.min_exp_num_ticks = exp_num_ticks_constraints[0]
            self.max_exp_num_ticks = exp_num_ticks_constraints[1]

    def _get_exp_num_ticks(self):
        prev_num_of_ticks = self.imbalance_tick_statistics['num_ticks_bar']
        exp_num_ticks = ewma(np.array(
            prev_num_of_ticks[-self.num_prev_bars:], dtype=float), self.num_prev_bars)[-1]
        return min(max(exp_num_ticks, self.min_exp_num_ticks), self.max_exp_num_ticks)


class ConstRunBars(BaseRunBars):
    """
    Contains all of the logic to construct the imbalance bars with fixed expected number of ticks. This class shouldn't
    be used directly. We have added functions to the package such as get_const_dollar_imbalance_bars which will create
    an instance of this class and then construct the imbalance bars, to return to the user.

    This is because we wanted to simplify the logic as much as possible, for the end user.
    """

    def __init__(self, file_path_or_df, metric, num_prev_bars, expected_imbalance_window, exp_num_ticks_init, batch_size,
                 analyse_thresholds):
        """
        Constructor

        :param file_path_or_df: (String) Path to the csv file or Pandas Data Frame containing raw tick data in the format[date_time, price, volume]
        :param metric: (String) type of run bar to create. Example: "dollar_run"
        :param num_prev_bars: (Int) Window size for E[T]s (number of previous bars to use for expected number of ticks estimation)
        :param expected_imbalance_window: (Int) EMA window used to estimate expected run
        :param exp_num_ticks_init: (Int) Initial number of expected ticks
        :param batch_size: (Int) Number of rows to read in from the csv, per batch
        :param analyse_thresholds: (Boolean) Flag to save  and return thresholds used to sample run bars
        """
        BaseRunBars.__init__(self, file_path_or_df, metric, batch_size, num_prev_bars, expected_imbalance_window,
                             exp_num_ticks_init,
                             analyse_thresholds)

    def _get_exp_num_ticks(self):
        return self.thresholds['exp_num_ticks']


def get_ema_dollar_run_bars(file_path_or_df, num_prev_bars=3, expected_imbalance_window=10000, exp_num_ticks_init=20000,
                            exp_num_ticks_constraints=None, batch_size=2e7, analyse_thresholds=False,
                            verbose=True, to_csv=False, output_path=None):
    """
    Creates the EMA dollar run bars: date_time, open, high, low, close, volume.

    :param file_path_or_df: File path pointing to csv data.
    :param num_prev_bars: (Int) Window size for E[T]s (number of previous bars to use for expected number of ticks estimation)
    :param expected_imbalance_window: (Int) EMA window used to estimate expected run
    :param exp_num_ticks_init: initial expected number of ticks per bar
    :param exp_num_ticks_constraints (Array) Minimum and maximum possible number of expected ticks. Used to control bars sampling convergence
    :param batch_size: The number of rows per batch. Less RAM = smaller batch size.
    :param verbose: Print out batch numbers (True or False)
    :param to_csv: Save bars to csv after every batch run (True or False)
    :param analyse_thresholds: (Boolean) Flag to save  and return thresholds used to sample run bars
    :param output_path: Path to csv file, if to_csv is True
    :return: DataFrame of dollar bars and DataFrame of thresholds
    """
    bars = EMARunBars(file_path_or_df=file_path_or_df, metric='dollar_run', num_prev_bars=num_prev_bars,
                      expected_imbalance_window=expected_imbalance_window,
                      exp_num_ticks_init=exp_num_ticks_init, exp_num_ticks_constraints=exp_num_ticks_constraints,
                      batch_size=batch_size, analyse_thresholds=analyse_thresholds)
    run_bars = bars.batch_run(
        verbose=verbose, to_csv=to_csv, output_path=output_path)

    return run_bars, pd.DataFrame(bars.bars_thresholds)


def get_ema_volume_run_bars(file_path_or_df, num_prev_bars=3, expected_imbalance_window=10000, exp_num_ticks_init=20000,
                            exp_num_ticks_constraints=None, batch_size=2e7, analyse_thresholds=False,
                            verbose=True, to_csv=False, output_path=None):
    """
    Creates the EMA volume run bars: date_time, open, high, low, close, volume.

    :param file_path_or_df: File path pointing to csv data.
    :param num_prev_bars: (Int) Window size for E[T]s (number of previous bars to use for expected number of ticks estimation)
    :param expected_imbalance_window: (Int) EMA window used to estimate expected run
    :param exp_num_ticks_init: initial expected number of ticks per bar
    :param exp_num_ticks_constraints (Array) Minimum and maximum possible number of expected ticks. Used to control bars sampling convergence
    :param batch_size: The number of rows per batch. Less RAM = smaller batch size.
    :param verbose: Print out batch numbers (True or False)
    :param to_csv: Save bars to csv after every batch run (True or False)
    :param analyse_thresholds: (Boolean) Flag to save  and return thresholds used to sample run bars
    :param output_path: Path to csv file, if to_csv is True
    :return: DataFrame of volume bars and DataFrame of thresholds
    """
    bars = EMARunBars(file_path_or_df=file_path_or_df, metric='volume_run', num_prev_bars=num_prev_bars,
                      expected_imbalance_window=expected_imbalance_window,
                      exp_num_ticks_init=exp_num_ticks_init, exp_num_ticks_constraints=exp_num_ticks_constraints,
                      batch_size=batch_size, analyse_thresholds=analyse_thresholds)
    run_bars = bars.batch_run(
        verbose=verbose, to_csv=to_csv, output_path=output_path)

    return run_bars, pd.DataFrame(bars.bars_thresholds)


def get_ema_tick_run_bars(file_path_or_df, num_prev_bars=3, expected_imbalance_window=10000, exp_num_ticks_init=20000,
                          exp_num_ticks_constraints=None, batch_size=2e7, analyse_thresholds=False,
                          verbose=True, to_csv=False, output_path=None):
    """
    Creates the EMA tick run bars: date_time, open, high, low, close, volume.

    :param file_path_or_df: File path pointing to csv data.
    :param num_prev_bars: (Int) Window size for E[T]s (number of previous bars to use for expected number of ticks estimation)
    :param expected_imbalance_window: (Int) EMA window used to estimate expected run
    :param exp_num_ticks_init: initial expected number of ticks per bar
    :param exp_num_ticks_constraints (Array) Minimum and maximum possible number of expected ticks. Used to control bars sampling convergence
    :param batch_size: The number of rows per batch. Less RAM = smaller batch size.
    :param verbose: Print out batch numbers (True or False)
    :param to_csv: Save bars to csv after every batch run (True or False)
    :param analyse_thresholds: (Boolean) Flag to save  and return thresholds used to sample run bars
    :param output_path: Path to csv file, if to_csv is True
    :return: DataFrame of tick bars and DataFrame of thresholds
    """
    bars = EMARunBars(file_path_or_df=file_path_or_df, metric='tick_run', num_prev_bars=num_prev_bars,
                      expected_imbalance_window=expected_imbalance_window,
                      exp_num_ticks_init=exp_num_ticks_init, exp_num_ticks_constraints=exp_num_ticks_constraints,
                      batch_size=batch_size, analyse_thresholds=analyse_thresholds)
    run_bars = bars.batch_run(
        verbose=verbose, to_csv=to_csv, output_path=output_path)

    return run_bars, pd.DataFrame(bars.bars_thresholds)


def get_const_dollar_run_bars(file_path_or_df, num_prev_bars, expected_imbalance_window=10000, exp_num_ticks_init=20000,
                              batch_size=2e7, analyse_thresholds=False, verbose=True, to_csv=False,
                              output_path=None):
    """
    Creates the Const dollar run bars: date_time, open, high, low, close, volume.

    :param file_path_or_df: File path pointing to csv data.
    :param num_prev_bars: (Int) Window size for estimating buy ticks proportion (number of previous bars to use in EWMA)
    :param expected_imbalance_window: (Int) EMA window used to estimate expected imbalance
    :param exp_num_ticks_init: initial expected number of ticks per bar
    :param batch_size: The number of rows per batch. Less RAM = smaller batch size.
    :param verbose: Print out batch numbers (True or False)
    :param to_csv: Save bars to csv after every batch run (True or False)
    :param analyse_thresholds: (Boolean) Flag to save  and return thresholds used to sample run bars
    :param output_path: Path to csv file, if to_csv is True
    :return: DataFrame of dollar bars and DataFrame of thresholds
    """
    bars = ConstRunBars(file_path_or_df=file_path_or_df, metric='dollar_run', num_prev_bars=num_prev_bars,
                        expected_imbalance_window=expected_imbalance_window,
                        exp_num_ticks_init=exp_num_ticks_init,
                        batch_size=batch_size, analyse_thresholds=analyse_thresholds)
    run_bars = bars.batch_run(
        verbose=verbose, to_csv=to_csv, output_path=output_path)

    return run_bars, pd.DataFrame(bars.bars_thresholds)


def get_const_volume_run_bars(file_path_or_df, num_prev_bars, expected_imbalance_window=10000, exp_num_ticks_init=20000,
                              batch_size=2e7, analyse_thresholds=False, verbose=True, to_csv=False,
                              output_path=None):
    """
    Creates the Const volume run bars: date_time, open, high, low, close, volume.

    :param file_path_or_df: File path pointing to csv data.
    :param num_prev_bars: (Int) Window size for estimating buy ticks proportion (number of previous bars to use in EWMA)
    :param expected_imbalance_window: (Int) EMA window used to estimate expected imbalance
    :param exp_num_ticks_init: initial expected number of ticks per bar
    :param batch_size: The number of rows per batch. Less RAM = smaller batch size.
    :param verbose: Print out batch numbers (True or False)
    :param to_csv: Save bars to csv after every batch run (True or False)
    :param analyse_thresholds: (Boolean) Flag to save  and return thresholds used to sample run bars
    :param output_path: Path to csv file, if to_csv is True
    :return: DataFrame of volume bars and DataFrame of thresholds
    """
    bars = ConstRunBars(file_path_or_df=file_path_or_df, metric='volume_run', num_prev_bars=num_prev_bars,
                        expected_imbalance_window=expected_imbalance_window,
                        exp_num_ticks_init=exp_num_ticks_init,
                        batch_size=batch_size, analyse_thresholds=analyse_thresholds)
    run_bars = bars.batch_run(
        verbose=verbose, to_csv=to_csv, output_path=output_path)

    return run_bars, pd.DataFrame(bars.bars_thresholds)


def get_const_tick_run_bars(file_path_or_df, num_prev_bars, expected_imbalance_window=10000, exp_num_ticks_init=20000,
                            batch_size=2e7, analyse_thresholds=False, verbose=True, to_csv=False,
                            output_path=None):
    """
    Creates the Const tick run bars: date_time, open, high, low, close, volume.

    :param file_path_or_df: File path pointing to csv data.
    :param num_prev_bars: (Int) Window size for estimating buy ticks proportion (number of previous bars to use in EWMA)
    :param expected_imbalance_window: (Int) EMA window used to estimate expected imbalance
    :param exp_num_ticks_init: initial expected number of ticks per bar
    :param batch_size: The number of rows per batch. Less RAM = smaller batch size.
    :param verbose: Print out batch numbers (True or False)
    :param to_csv: Save bars to csv after every batch run (True or False)
    :param analyse_thresholds: (Boolean) Flag to save  and return thresholds used to sample run bars
    :param output_path: Path to csv file, if to_csv is True
    :return: DataFrame of tick bars and DataFrame of thresholds
    """
    bars = ConstRunBars(file_path_or_df=file_path_or_df, metric='tick_run', num_prev_bars=num_prev_bars,
                        expected_imbalance_window=expected_imbalance_window,
                        exp_num_ticks_init=exp_num_ticks_init,
                        batch_size=batch_size, analyse_thresholds=analyse_thresholds)
    run_bars = bars.batch_run(
        verbose=verbose, to_csv=to_csv, output_path=output_path)

    return run_bars, pd.DataFrame(bars.bars_thresholds)
