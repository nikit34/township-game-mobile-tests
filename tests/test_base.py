import functools
import time

from configs.images.checker_config import ImagesCheckerConfig
from src.file_manager import FileManager


class TestBase:
    @classmethod
    def setup_class(cls):
        file_manager = FileManager()
        file_manager.remove("image/tmp_images")

        cls.tolerance = ImagesCheckerConfig.get_tolerance()

    @staticmethod
    def _is_within_bounds(cluster, expected_cluster, tolerance):
        ((x_min1, y_min1), (x_max1, y_max1)) = cluster
        ((x_min2, y_min2), (x_max2, y_max2)) = expected_cluster

        return (
            abs(x_min1 - x_min2) <= tolerance and
            abs(y_min1 - y_min2) <= tolerance and
            abs(x_max1 - x_max2) <= tolerance and
            abs(y_max1 - y_max2) <= tolerance
        )

    def check_clusters(self, detected_clusters, expected_clusters):
        if not detected_clusters:
            raise AssertionError("No clusters were found")

        detected_clusters_sorted = sorted(detected_clusters, key=lambda cluster: cluster[0][0])
        expected_clusters_sorted = sorted(expected_clusters, key=lambda cluster: cluster[0][0])

        for detected, expected in zip(detected_clusters_sorted, expected_clusters_sorted):
            if not self._is_within_bounds(detected, expected, self.tolerance):
                raise AssertionError("Cluster " + str(detected) + " is out of bounds " + str(expected) + "\n" +
                                     "detected_clusters_sorted=" + str(detected_clusters_sorted) + "\n" +
                                     "expected_clusters_sorted=" + str(expected_clusters_sorted))

    def wait_load(self, timeout=5):
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                while time.time() - start_time < timeout:
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        print("Exception caught: " + str(e) + "\nRetrying...")
                        time.sleep(1)
                raise TimeoutError("Function " + func.__name__ + " did not complete in " + str(timeout) + " seconds")
            return wrapper
        return decorator

