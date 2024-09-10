import numpy as np

def poly2xyxy(poly):
   
   """
    Convert a polygon representation to an axis-aligned bounding box.

    This function takes a list of vertices (x, y) of a polygon and calculates the minimum and 
    maximum x and y coordinates. The result is a bounding box (xmin, ymin, xmax, ymax) that 
    tightly encloses the polygon.

    Parameters:
    - poly (List[Tuple[int, int]]): A list of tuples, where each tuple represents a vertex (x, y) of the polygon.

    Returns:
    - Tuple[int, int, int, int]: A tuple representing the bounding box (xmin, ymin, xmax, ymax) of the polygon.
    """
   poly = np.array(poly)
   return (min(poly[:, 0]), min(poly[:, 1]), max(poly[:, 0]), max(poly[:, 1]))


def xyxy2xyxyn(xyxy, image_shape):
    """
    Convert bounding box coordinates from pixel format to normalized format.

    This function normalizes the bounding box coordinates based on the image dimensions. 
    The pixel coordinates (xmin, ymin, xmax, ymax) are converted to a normalized format 
    where each coordinate is represented as a fraction of the image's width or height.

    Parameters:
    - xyxy (tuple): A tuple of four integers (xmin, ymin, xmax, ymax) representing the bounding box coordinates in pixel format.
    - image_shape (tuple): A tuple of two integers (height, width) representing the dimensions of the image.

    Returns:
    - tuple: A tuple of four floats (xmin_n, ymin_n, xmax_n, ymax_n) representing the normalized bounding box coordinates.
    """
    xmin, ymin, xmax, ymax = xyxy
    return (xmin / image_shape[1], ymin / image_shape[0], xmax / image_shape[1], ymax / image_shape[0])


