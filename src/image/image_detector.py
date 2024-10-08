import cv2
import numpy as np
from sklearn.cluster import DBSCAN
from configs.images.detector_config import ImagesDetectorConfig


class ImageDetector:
    def __init__( self, name_target, save_img=True):
        config = ImagesDetectorConfig(name_target)

        self.n_octave_layers = config.get_n_octave_layers()
        self.contrast_threshold = config.get_contrast_threshold()
        self.eps = config.get_eps()
        self.clahe_clip_limit = config.get_clahe_clip_limit()
        self.clahe_grid_size = config.get_clahe_grid_size()
        self.min_cluster_area = config.get_min_cluster_area()
        self.min_samples = config.get_min_samples()
        self.ransac = config.get_ransac()
        self.ransac_threshold = config.get_ransac_threshold()

        self.save_img = save_img

    def apply_clahe(self, image):
        clahe = cv2.createCLAHE(clipLimit=self.clahe_clip_limit, tileGridSize=self.clahe_grid_size)
        return clahe.apply(image)

    def increase_contrast(self, image):
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=self.clahe_clip_limit, tileGridSize=self.clahe_grid_size)
        l = clahe.apply(l)
        lab = cv2.merge((l, a, b))
        return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

    def compute_sift_keypoints_and_descriptors(self, gray_image):
        sift = cv2.SIFT_create(
            nOctaveLayers=self.n_octave_layers,
            contrastThreshold=self.contrast_threshold,
            edgeThreshold=0,
            nfeatures=0,
            sigma=1.8,
            descriptorType=cv2.CV_32F
        )
        keypoints, descriptors = sift.detectAndCompute(gray_image, None)
        if descriptors is None:
            return [], None
        return keypoints, descriptors

    @staticmethod
    def match_descriptors(des1, des2):
        bf = cv2.BFMatcher(cv2.NORM_L2)
        matches = bf.match(des1, des2)
        return sorted(matches, key=lambda x: x.distance)

    @staticmethod
    def extract_coordinates_from_matches(matches, keypoints):
        coordinates = []
        for match in matches:
            x, y = keypoints[match.trainIdx].pt
            coordinates.append((int(x), int(y)))
        return coordinates

    def perform_clustering(self, coordinates, custom_min_samples=None):
        if len(coordinates) > 0:
            coordinates = np.array(coordinates)
            if custom_min_samples is None:
                custom_min_samples = self.min_samples
            clustering = DBSCAN(eps=self.eps, min_samples=custom_min_samples, algorithm='brute').fit(coordinates)
            cluster_labels = clustering.labels_
            return cluster_labels
        else:
            return []

    def get_cluster_bounds(self, coordinates, cluster_labels):
        cluster_bounds = []
        unique_labels = set(cluster_labels) - {-1}

        coordinates = np.array(coordinates)

        for label in unique_labels:
            cluster_points = coordinates[cluster_labels == label]
            x_min, y_min = np.min(cluster_points, axis=0)
            x_max, y_max = np.max(cluster_points, axis=0)
            width = x_max - x_min
            height = y_max - y_min
            area = width * height

            if area >= self.min_cluster_area:
                cluster_bounds.append(((int(x_min), int(y_min)), (int(x_max), int(y_max))))

        return cluster_bounds

    @staticmethod
    def draw_clusters_and_points(image, cluster_bounds, coordinates, cluster_labels):
        coordinates = np.array(coordinates)

        for i, ((x_min, y_min), (x_max, y_max)) in enumerate(cluster_bounds, start=1):
            cv2.rectangle(image, (x_min, y_min), (x_max, y_max), (255, 0, 0), 2)
            label_position = (x_min, y_min - 10) if y_min - 10 > 0 else (x_min, y_min + 10)
            cv2.putText(image, str(i), label_position, cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

        clustered_coords = coordinates[cluster_labels != -1]
        if clustered_coords.size:
            for x, y in clustered_coords:
                cv2.circle(image, (x, y), 3, (0, 255, 0), -1)

        noise_coords = coordinates[cluster_labels == -1]
        if noise_coords.size:
            for x, y in noise_coords:
                cv2.circle(image, (x, y), 3, (0, 0, 255), -1)

    @staticmethod
    def convert_to_color_if_needed(image):
        if image.ndim == 2:
            return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        return image

    def apply_ransac(self, kp1, kp2, matches):
        if len(matches) < 4:
            return []

        src_pts = np.float32([kp1[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp2[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)

        M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, self.ransac_threshold)
        matchesMask = mask.ravel().tolist()

        good_matches = [m for i, m in enumerate(matches) if matchesMask[i] == 1]
        if M is None or len(good_matches) < 4:
            return []
        return good_matches

    def get_good_matches_from_clusters(self, kp1, kp2, matches, cluster_labels):
        all_good_matches = []
        for cluster in set(cluster_labels):
            if cluster == -1:
                continue

            cluster_matches = [m for i, m in enumerate(matches) if cluster_labels[i] == cluster]

            good_matches = self.apply_ransac(kp1, kp2, cluster_matches)
            all_good_matches.extend(good_matches)

        return all_good_matches

    def get_coordinates_objects(self, original_img, template_img):
        original_img.cv_image = self.convert_to_color_if_needed(original_img.cv_image)
        template_img.cv_image = self.convert_to_color_if_needed(template_img.cv_image)

        original_img.cv_image = self.increase_contrast(original_img.cv_image)
        template_img.cv_image = self.increase_contrast(template_img.cv_image)

        gray_original = cv2.cvtColor(original_img.cv_image, cv2.COLOR_BGR2GRAY)
        gray_template = cv2.cvtColor(template_img.cv_image, cv2.COLOR_BGR2GRAY)

        gray_original = self.apply_clahe(gray_original)
        gray_template = self.apply_clahe(gray_template)

        kp1, des1 = self.compute_sift_keypoints_and_descriptors(gray_template)
        kp2, des2 = self.compute_sift_keypoints_and_descriptors(gray_original)

        matches = self.match_descriptors(des1, des2)

        coordinates = self.extract_coordinates_from_matches(matches, kp2)
        cluster_labels = self.perform_clustering(coordinates)

        if self.ransac:
            good_matches = self.get_good_matches_from_clusters(kp1, kp2, matches, cluster_labels)
            coordinates = self.extract_coordinates_from_matches(good_matches, kp2)
            cluster_labels = self.perform_clustering(coordinates, custom_min_samples=1)

        cluster_bounds = self.get_cluster_bounds(coordinates, cluster_labels)

        self.draw_clusters_and_points(original_img.cv_image, cluster_bounds, coordinates, cluster_labels)

        if self.save_img:
            original_img.save("detected")
            template_img.save("template")

        return cluster_bounds
