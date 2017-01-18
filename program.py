import os
import random
import time

from circuit_breaker import CircuitBreaker, CircuitOpenException


CONSOLE_GREEN = '\033[92m'
CONSOLE_RED = '\033[91m'
CONSOLE_WHITE = '\033[39m'
HTTP_BIN_URL = 'http://httpbin.org/status/'


def main():
    breaker = CircuitBreaker(threshold=5, window=5)
    bad_good_ratio = 0.2  # Percentage of 500s (vs 200s)

    while True:
        schmutz = random.random()
        if schmutz <= bad_good_ratio:
            status_code = 500
        else:
            status_code = 200

        try:
            breaker.get(HTTP_BIN_URL + str(status_code))
            is_circuit_closed = True
        except CircuitOpenException:
            is_circuit_closed = False

        print_buckets(breaker, is_circuit_closed)


def print_buckets(breaker, is_circuit_closed):
    """
    Prints bucket information.

    Example output:

    current time: Thu Jan  5 16:25:19 2017
    current window: 1483629914 - 1483629919
    circuit state: closed

    BUCKET_TS       ERROR_COUNT     WITHIN_WINDOW
    0               0               no
    1483629916      1               yes
    0               0               no
    1483629918      1               yes
    1483629919      1               yes
    """
    os.system('clear')

    # Assign preamble and header values
    current_time = int(time.time())
    window_lower_bound = current_time - breaker.error_window
    headers = ['BUCKET_TS', 'ERROR_COUNT', 'WITHIN_WINDOW']

    # Print the preamble and table headers
    def circuit_state_label():
        if is_circuit_closed is True:
            return CONSOLE_GREEN + 'closed' + CONSOLE_WHITE
        else:
            return CONSOLE_RED + 'open' + CONSOLE_WHITE

    print 'current time: %s' % time.ctime(current_time)
    print 'current window: %s - %s' % (window_lower_bound, current_time)
    print 'circuit state: %s' % circuit_state_label()
    print
    print '{:<15} {:<15} {:<15}'.format(*headers)

    def relative_time_label(bucket):
        if bucket.ts == 0 or current_time - bucket.ts == 0:
            return '0'
        else:
            return '-%d' % (current_time - bucket.ts)

    def within_window_prefix(within_window):
        if within_window is True:
            return '\033[33m'
        else:
            return '\033[39m'

    # Print the table rows
    for bucket in breaker.buckets:
        relative_time = relative_time_label(bucket)
        within_window = current_time - bucket.ts <= breaker.error_window
        within_window_label = 'yes' if within_window is True else 'no'
        format_args = [within_window_prefix(within_window), relative_time,
                       bucket.count, within_window_label]
        print '{!s}{:<15} {:<15} {:<15}\033[39m'.format(*format_args)

    print


if __name__ == '__main__':
    main()
