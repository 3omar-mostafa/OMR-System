import numpy as np
import cv2
import math


# Fixing Orientation Step (Fixing Rotation and Perspective and Crop)
# Assuming we get a binary image
def fix_orientation(img: np.ndarray) -> np.ndarray:
    if img.dtype == np.bool:
        img = img.astype(np.uint8) * 255

    img = cv2.bitwise_not(img)
    img = __crop_borders(img)
    angle = __get_rotation_angle(img)

    img_rotated = __rotate_image(img, angle)
    img_rotated = __crop_image(img_rotated)
    (height, width) = img_rotated.shape

    transformation_matrix = get_perspective_transformation_matrix(img_rotated)
    img_perspective = cv2.warpPerspective(img_rotated, transformation_matrix, (width, height))

    return cv2.bitwise_not(img_perspective)


def __rotate_image(img: np.ndarray, angle_in_degrees) -> np.ndarray:
    (height, width) = img.shape[:2]
    center = (width // 2, height // 2)
    rotation_matrix = cv2.getRotationMatrix2D(center, angle_in_degrees, scale=1)
    return cv2.warpAffine(img, rotation_matrix, (width, height), borderValue=0)


def __crop_borders(img: np.ndarray, percentage: float = 0.01) -> np.ndarray:
    (h, w) = img.shape[:2]
    delta_h = int(percentage * h)
    delta_w = int(percentage * w)
    return img[delta_h:h - delta_h, delta_w:w - delta_w]


def __get_line_length(line):
    x1, y1, x2, y2 = np.array(line.copy()).flatten()
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


# Get Line's slope angle in degrees
def __get_line_angle(line):
    x1, y1, x2, y2 = np.array(line.copy()).flatten()
    x = x2 - x1
    y = y2 - y1
    return math.degrees(math.atan2(y, x))


def __get_bounding_lines(hull_points) -> list:
    hull_points = np.append(hull_points, [hull_points[0]], axis=0)

    lines = [[hull_points[0], hull_points[1]]]
    old_angle = __get_line_angle(lines[0])
    for i in range(2, len(hull_points)):
        line = [hull_points[i - 1], hull_points[i]]
        new_angle = abs(__get_line_angle(line))
        if abs(old_angle - new_angle) <= 15:
            lines[-1][1] = hull_points[i]
        else:
            lines.append(line)
        old_angle = abs(__get_line_angle(lines[-1]))

    lines.sort(key=__get_line_length, reverse=True)
    return lines[0:4]


# Return Top-Left , Top-Right , Bottom-Right , Bottom-Left boundary boundary points
# They are used for perspective fixing, therefore we use only left and right lines to get points
# Left have min sum of x , right have max sum of x
# Top have min sum of y , Bottom have max sum of y
def __get_boundary_points(boundary_lines: list) -> np.ndarray:
    boundary_lines = np.array(boundary_lines)
    sum: np.ndarray = boundary_lines.sum(axis=1)
    sum = sum.reshape((4, 2))

    min_x_index = np.argmin(sum, axis=0)[0]
    max_x_index = np.argmax(sum, axis=0)[0]

    left = boundary_lines[min_x_index].reshape((2, 2))
    right = boundary_lines[max_x_index].reshape((2, 2))

    left_sum = np.sum(left, axis=1)
    right_sum = np.sum(right, axis=1)

    top_left = left[np.argmin(left_sum, axis=0)]
    bottom_left = left[np.argmax(left_sum, axis=0)]
    top_right = right[np.argmin(right_sum, axis=0)]
    bottom_right = right[np.argmax(right_sum, axis=0)]

    return np.array([top_left, top_right, bottom_right, bottom_left], dtype=np.float32)


# Line is defined by s (starting point) , e (ending point)
def __get_intersection(line1, line2):
    s1, e1 = np.array(line1, dtype=float).reshape((2, 2))
    s2, e2 = np.array(line2, dtype=float).reshape((2, 2))

    x = s2 - s1
    direction1 = e1 - s1
    direction2 = e2 - s2

    cross_product = direction1[0] * direction2[1] - direction1[1] * direction2[0]

    # if lines are parallel there is no intersection
    if abs(cross_product) < 0.0000001:
        raise ArithmeticError

    t1 = (x[0] * direction2[1] - x[1] * direction2[0]) / cross_product
    return s1 + direction1 * t1


def get_perspective_transformation_matrix(img: np.ndarray) -> np.ndarray:
    all_points = cv2.findNonZero(img)
    hull_points: np.ndarray = cv2.convexHull(all_points)

    bounding_lines = __get_bounding_lines(hull_points)
    bounding_points = __get_boundary_points(bounding_lines)

    x, y, w, h = cv2.boundingRect(hull_points)

    rectangle_points = np.float32([[x, y], [x + w, y], [x + w, y + h], [x, y + h]])
    transformation_matrix = cv2.getPerspectiveTransform(bounding_points, rectangle_points)
    return transformation_matrix


def __crop_image(binary_image: np.ndarray):
    blurred = cv2.medianBlur(binary_image, 9)
    all_points = cv2.findNonZero(blurred)
    x, y, w, h = cv2.boundingRect(all_points)
    binary_image = binary_image[y: (y + h), x:(x + w)]
    border_x = binary_image.shape[1] // 10
    border_y = binary_image.shape[0] // 5
    return cv2.copyMakeBorder(binary_image, border_y, border_y, border_x, border_x, cv2.BORDER_CONSTANT, value=0)


def __get_rotation_angle(binary_image: np.ndarray):
    img = cv2.medianBlur(binary_image, 9)
    all_points = cv2.findNonZero(img)
    center, (width, height), angle = cv2.minAreaRect(all_points)

    if width < height:
        angle += 90

    return angle