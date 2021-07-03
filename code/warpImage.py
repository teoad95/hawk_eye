import numpy as np
import cv2
from matplotlib import path
import matplotlib.pyplot as plt
from perturb_functions.pan import pan
from perturb_functions.zoom import zoom
from perturb_functions.tilt import tilt

def getMask(points, x_min, x_max, y_min, y_max):
    x_width = int(x_max - x_min + 1)
    y_width = int(y_max - y_min + 1)
    # points are in the order TL, TR, BR, BL
    mask = np.zeros((x_width, y_width))
    p = path.Path([list(cood) for cood in points])
    for i in range(mask.shape[1]):
        for j in range(mask.shape[0]):
            if p.contains_point([i, j]):
                mask[i, j] = 1
    mask = mask.T
    return mask


def get_bounds(transformed_corners, footballIm, padding):
    x_min = min(0, min(transformed_corners[0, :]))
    x_max = max(footballIm.shape[1], max(transformed_corners[0, :]))
    y_min = min(0, min(transformed_corners[1, :]))
    y_max = max(footballIm.shape[0], max(transformed_corners[1, :]))

    x_min -= padding
    y_min -= padding
    x_max += padding
    y_max += padding

    return x_min, x_max, y_min, y_max


def apply_pan(shifted_corners, non_homo_corners, inputIm_shape, canvasIm):
    pert_points = np.array(pan(shifted_corners, delta_theta=0.18))
    # Create mask for perturbed trapezium
    # mask = getMask(pert_points, x_min, x_max, y_min, y_max)
    H_perturb = cv2.findHomography(non_homo_corners, pert_points)[0]
    edge_map_perturb = get_edge_map(inputIm_shape, canvasIm, H_perturb)
    return edge_map_perturb, H_perturb


def apply_zoom(shifted_corners, non_homo_corners, inputIm_shape, canvasIm):
    pert_points = np.array(zoom(shifted_corners, sx=0.85, sy=0.85))
    # Create mask for perturbed trapezium
    # mask = getMask(pert_points, x_min, x_max, y_min, y_max)
    H_perturb = cv2.findHomography(non_homo_corners, pert_points)[0]
    edge_map_perturb = get_edge_map(inputIm_shape, canvasIm, H_perturb)
    return edge_map_perturb, H_perturb

def apply_tilt(shifted_corners, non_homo_corners, inputIm_shape, canvasIm):
    pert_points = np.array(tilt(shifted_corners,t=0.035))
    # Create mask for perturbed trapezium
    # mask = getMask(pert_points, x_min, x_max, y_min, y_max)
    H_perturb = cv2.findHomography(non_homo_corners, pert_points)[0]
    edge_map_perturb = get_edge_map(inputIm_shape, canvasIm, H_perturb)
    return edge_map_perturb, H_perturb

def apply_perturbation(corners, transformed_corners, canvasIm, inputIm,
                       x_min, x_max, y_min, y_max):
    '''
    This is the wrapper function that creates all sorts of perturbations
    to the warped input image and finds the homographies that map it back
    a rectangle of the input shape. In doing so, we create a dictionary
    of edgeMap -> homography (camera view to top view)
    '''
    # Need to shift corners to map them to the canvas with H
    shifted_corners = np.array([[corner[0] - x_min, corner[1] - y_min]
                                for corner in transformed_corners.T])

    # Find the H for rect to perturbed trapezium
    non_homo_corners = np.array([[corner[0], corner[1]]
                                 for corner in corners.T])
    plt.imshow(inputIm.astype('uint8'))
    plt.title("InputIm")
    plt.show()

    # First pair is directly the edge map for inputIm and the homography
    H_base = cv2.findHomography(non_homo_corners, shifted_corners)[0]
    edge_map = get_edge_map(inputIm.shape, canvasIm, H_base)
    plt.imshow(edge_map.astype('uint8'))
    plt.title("Original")
    plt.show()

    # Generate more pairs for different perturbations
    # Get trapezium after applying zoom perturbation
    edge_map_zoom, H_zoom = apply_zoom(
        shifted_corners, non_homo_corners, inputIm.shape, canvasIm)
    plt.imshow(edge_map_zoom.astype('uint8'))
    plt.title("Zoom")
    plt.show()

    # Get trapezium after applying pan perturbation
    edge_map_pan, H_pan = apply_pan(
        shifted_corners, non_homo_corners, inputIm.shape, canvasIm)
    plt.imshow(edge_map_pan.astype('uint8'))
    plt.title("Pan")
    plt.show()

    # Get trapezium after applying tilt perturbation
    edge_map_tilt, H_tilt = apply_tilt(
        shifted_corners, non_homo_corners, inputIm.shape, canvasIm)
    plt.imshow(edge_map_tilt.astype('uint8'))
    plt.title("Tilt")
    plt.show()


def warpImageOntoCanvas(inputIm, footballIm, H, x_min, x_max, y_min, y_max):
    x_width = int(x_max - x_min + 1)
    y_width = int(y_max - y_min + 1)
    canvasIm = np.zeros((y_width, x_width, 3))

    xs, ys, a = [], [], np.zeros((x_width, y_width))
    for index, _ in np.ndenumerate(a):
        xs.append(x_min + index[0]), ys.append(y_min + index[1])
    canvas_coords = np.vstack(
        (np.array(xs), np.array(ys), np.ones(len(xs))))
    transformed = np.matmul(np.linalg.inv(H), canvas_coords)
    xs = np.divide(transformed[0, :], transformed[2, :])
    ys = np.divide(transformed[1, :], transformed[2, :])
    inputIm_coords = np.transpose(np.column_stack((xs, ys)))

    def inside_input(x, y):
        return x >= 0 and x < inputIm.shape[1] and \
            y >= 0 and y < inputIm.shape[0]

    # Uncomment if you want to plot the warped image on the canvas

    # for k in range(0, canvas_coords.shape[1]):
    #     x_canvas = int(canvas_coords[0, k] - x_min)
    #     y_canvas = int(canvas_coords[1, k] - y_min)
    #     x_input, y_input = int(inputIm_coords[0, k]), int(inputIm_coords[1, k])
    #     if inside_input(x_input, y_input):
    #         # Copy input image to refIm
    #         canvasIm[y_canvas, x_canvas] = inputIm[y_input, x_input]

    footballIm_h, footballIm_w, _ = footballIm.shape
    for i in range(footballIm_w):
        for j in range(footballIm_h):
            canvasIm[j - int(y_min)][i - int(x_min)] = footballIm[j][i]

    return canvasIm


def get_edge_map(inputIm_shape, canvasIm, H):
    '''
    Input: inputIn_shape- shape of the edge map returned
    canvasIm- top view canvas with only the football field on it
    H- the calculated homography (camera view -> top view)
    '''
    xs, ys, a = [], [], np.zeros((inputIm_shape[1], inputIm_shape[0]))
    for index, _ in np.ndenumerate(a):
        xs.append(index[0]), ys.append(index[1])
    input_coords = np.vstack(
        (np.array(xs), np.array(ys), np.ones(len(xs))))
    transformed = np.matmul(H, input_coords)
    transformed[0, :] = np.divide(transformed[0, :], transformed[2, :])
    transformed[1, :] = np.divide(transformed[1, :], transformed[2, :])

    edge_map_perturb = np.zeros(inputIm_shape)
    for k in range(0, input_coords.shape[1]):
        x_input = int(input_coords[0, k])
        y_input = int(input_coords[1, k])
        x_canvas = int(transformed[0, k])
        y_canvas = int(transformed[1, k])
        edge_map_perturb[y_input, x_input] = canvasIm[y_canvas, x_canvas]
    return edge_map_perturb


def warpImage(inputIm, footballIm, H, padding):
    h, w, _ = inputIm.shape
    # Find input image corners
    corners = np.array([[0, 0, 1], [w - 1, 0, 1],
                        [w - 1, h - 1, 1], [0, h - 1, 1]]).transpose()
    # Find trapezium corners in the warped space (top-view)
    transformed_corners = np.matmul(H, corners)
    transformed_corners = np.divide(
        transformed_corners, transformed_corners[2, :])

    # Get bounds with football field added and padding
    x_min, x_max, y_min, y_max = get_bounds(
        transformed_corners, footballIm, padding)

    # Get canvas with warped input and football field
    canvasIm = warpImageOntoCanvas(
        inputIm, footballIm, H, x_min, x_max, y_min, y_max)

    # Get the perturbation, mask and perturbed edge map in input space
    apply_perturbation(corners, transformed_corners, canvasIm,
                       inputIm, x_min, x_max, y_min, y_max)

    return canvasIm.astype('uint8')


def cv2warp(inputIm, H):
    w = 75
    h = 75
    warpIm = np.zeros((h, w, 3), "uint8")
    cv2.warpPerspective(
        src=inputIm, dst=warpIm, M=H, dsize=(h, w))


if __name__ == '__main__':
    #file_name = 'soccer_data/train_val/2'
    file_name = 'soccer_data/train_val/2'
    football_field = '/Users/thodoris/Documents/GitHub/Sport-analytics/Images/Highlights Real Madrid vs FC Barcelona (2-1)/frame42.jpg'

    with open('{}.homographyMatrix'.format(file_name)) as f:
        content = f.readlines()
    H = np.zeros((3, 3))
    for i in range(len(content)):
        H[i] = np.array([float(x) for x in content[i].strip().split()])
    bgr = cv2.imread('{}.jpg'.format(file_name)).astype(np.uint8)
    inputIm = bgr[..., ::-1]

    football = cv2.imread(football_field)
    football = football.astype(np.uint8)
    footballIm = football[..., ::-1]

    plt.imshow(footballIm)
    plt.show()
    warpIm = warpImage(
        bgr, footballIm, H, padding=200)

    # fig = plt.figure()
    # plt.imshow(inputIm)
    # plt.show()
    # plt.imshow(warpIm)
    # for (x, y) in pan_points:
    #     circle = plt.Circle((x, y), 2, color=(1, 0, 0), fill=True)
    #     fig.add_subplot().add_artist(circle)
    # plt.show()
    # plt.imshow(mask)
    # plt.show()
    # plt.imshow(edge_map_perturb)
    # plt.show()
