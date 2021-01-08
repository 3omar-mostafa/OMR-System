import argparse
import os
import cv2
import numpy as np


def get_command_line_args():
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument('input_path', help="Input Directory Containing Images, Or Image Filename")
    args_parser.add_argument('output_path', help="Output Directory, Or Output Filename")
    args_parser.add_argument("-d", "--debug", help="Enable Debug Mode", default=False, action="store_true")
    return args_parser.parse_args()


def get_filenames(path: str) -> list:
    if os.path.isfile(path):
        return [os.path.basename(path)]

    if os.path.isdir(path):
        return os.listdir(path)


def write_image(img: np.ndarray, directory: str, filename: str):
    if os.path.isdir(directory) and filename is not None:
        filename = os.path.join(directory, filename)
        cv2.imwrite(filename, img)
    elif filename is not None:
        os.mkdir(directory)
        filename = os.path.join(directory, filename)
        cv2.imwrite(filename, img)


def write_file(data: str, directory: str, filename: str):
    if os.path.isdir(directory) and filename is not None:
        filename = convert_extension(filename, "txt")
        filename = os.path.join(directory, filename)
        file = open(filename, 'a')
        file.write(data)
        file.close()


def convert_extension(filename: str, extension: str) -> str:
    filename = filename.split('.')[:-1]
    filename.append(f".{extension}")
    filename = ''.join(filename)
    return filename


def write_line_file(line: str, directory: str, filename: str):
    if os.path.isdir(directory) and filename is not None:
        filename = convert_extension(filename, "txt")
        filename = os.path.join(directory, filename)
        file = open(filename, 'a')
        file.writelines([line, '\n'])
        file.close()


def read_grayscale_image(input_path: str, filename: str) -> np.ndarray:
    if os.path.isfile(input_path):
        return cv2.imread(input_path, cv2.IMREAD_GRAYSCALE)
    elif os.path.isdir(input_path) and filename is not None:
        filename = os.path.join(input_path, filename)
        return cv2.imread(filename, cv2.IMREAD_GRAYSCALE)
