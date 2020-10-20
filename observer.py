"""
observer.py
Author: Michael Pagliaro
An observer module to attach listeners to python functions. Set the @observable decorator above a function that
can be observed, then the @observer() decorator over a function that will observe it. The observer will then be
called every time the observable function runs.
"""


# Dictionaries to hold the observers and their arguments
OBSERVER_DICT = dict()
ARGS_DICT = dict()


def observable(func):
    """
    A decorator set over functions that can be observed. When the observable function is called, it will first
    run, then call every function that is set as its observer.
    :param func: The function that is being observed.
    :return: A wrapper function to run around the observable function.
    """
    def wrapper_observable(*args, **kwargs):
        return_value = func(*args, **kwargs)
        if wrapper_observable in OBSERVER_DICT.keys():
            for observing_func in OBSERVER_DICT[wrapper_observable]:
                observing_func(*ARGS_DICT[(observing_func, wrapper_observable)][0],
                               **ARGS_DICT[(observing_func, wrapper_observable)][1])
        return return_value
    return wrapper_observable


def observer(observable_func, *observer_args, **observer_kwargs):
    """
    A decorator set over functions that will observe some other function and run every time it is called. The
    decorator itself takes arguments, first the function that it will observe, and after that an arbitrary number
    of arguments that will be passed to the observer each time it is run.
    :param observable_func: The function that this observer will listen to.
    :param observer_args: A list of arguments that will be passed to the observer.
    :param observer_kwargs: A list of keyword arguments that will be passed to the observer.
    :return: A wrapper function around the observer.
    """
    def decorator_observer(func):
        global OBSERVER_DICT
        global ARGS_DICT
        if observable_func in OBSERVER_DICT.keys():
            OBSERVER_DICT[observable_func].append(func)
        else:
            OBSERVER_DICT[observable_func] = [func]
        ARGS_DICT[(func, observable_func)] = (observer_args, observer_kwargs)

        def wrapper_observer(*args, **kwargs):
            return_value = func(*args, **kwargs)
            return return_value

        return wrapper_observer
    return decorator_observer
