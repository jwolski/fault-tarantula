import requests
import time

from bucket import Bucket
from circuit_errors import CircuitOpenException


class CircuitBreaker:
    def __init__(self, threshold, window):
        self.error_threshold = threshold
        self.error_window = window
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
        # Scan buckets within window and count errors
        current_time = int(time.time())
        num_errors_in_window = 0
        for bucket in self.buckets:
            if current_time - bucket.ts > self.error_window:
                continue
            num_errors_in_window += bucket.count

        return num_errors_in_window

    def is_circuit_open(self):
        """
        Returns True if circuit is open. Otherwise, returns False.
        """
        return self.count_errors_in_window() >= self.error_threshold
