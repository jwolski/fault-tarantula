import os
import random
import requests
import time


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
            breaker.get('http://httpbin.org/status/' + str(status_code))
            is_circuit_closed = True
        except CircuitOpenException:
            is_circuit_closed = False

        print_buckets(breaker, is_circuit_closed)


def print_buckets(breaker, is_circuit_closed):
    os.system('clear')

    # Preamble
    current_time = int(time.time())
    print 'current time: %s' % time.ctime(current_time)
    window_lower_bound = current_time - breaker.window
    print 'current window: %s - %s' % (window_lower_bound, current_time)
    circuit_state_label = 'closed' if is_circuit_closed is True else 'open'
    print 'circuit state: %s' % circuit_state_label
    print

    # Table Headers
    headers = ['BUCKET_TS', 'ERROR_COUNT', 'WITHIN_WINDOW']
    print '{:<15} {:<15} {:<15}'.format(*headers)

    # Table Rows
    for bucket in breaker.buckets:
        within_window = current_time - bucket.ts <= breaker.window
        within_window_label = 'yes' if within_window is True else 'no'
        format_args = [bucket.ts, bucket.count, within_window_label]
        print '{:<15} {:<15} {:<15}'.format(*format_args)

    print


class CircuitOpenException(Exception):
    pass


class Bucket:
    def __init__(self, ts, count):
        self.ts = ts
        self.count = count


class CircuitBreaker:
    def __init__(self, threshold, window):
        self.threshold = threshold
        self.window = window
        self.buckets = []

        num_buckets = window
        for i in range(0, num_buckets):
            self.buckets.append(Bucket(0, 0))

    def get(self, url):
        """
        Performs HTTP GET if circuit is closed. Otherwise, raises
        CircuitOpenException.
        """
        if self.is_circuit_open():
            raise CircuitOpenException

        response = requests.get(url)
        status_code_bucket = response.status_code / 100

        if status_code_bucket == 5:
            self.bump_error_count()

    def bump_error_count(self):
        """
        Bumps error count for bucket based on current time.
        """
        error_ts = int(time.time())
        bucket_index = error_ts % len(self.buckets)
        bucket = self.buckets[bucket_index]

        if bucket is None:
            pass  # panic

        if bucket.ts != error_ts:
            bucket.ts = error_ts
            bucket.count = 0

        bucket.count += 1

    def count_errors_in_window(self):
        """
        Counts number of errors appearing within error window.
        """
        current_time = int(time.time())
        bucket_index = current_time % len(self.buckets)
        bucket = self.buckets[bucket_index]

        # Scan buckets within window and count errors
        num_errors_in_window = 0
        for bucket in self.buckets:
            if current_time - bucket.ts > self.window:
                continue

            num_errors_in_window += bucket.count

        return num_errors_in_window

    def is_circuit_open(self):
        """
        Returns True if circuit is open. Otherwise, returns False.
        """
        return self.count_errors_in_window() >= self.threshold


if __name__ == '__main__':
    main()
