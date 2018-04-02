import scipy

import img_utils as imtil
import debug_utils as dbg
import numpy as np
from scipy import sparse

from scipy import special


def get_kernel(ker_params, angle, debug=False):
    """

    Calculates kernel

    Parameters
    ----------
    ker_params : KerParams
        kernel parameters
    angle : double
        retardation angle
    debug : bool
        is in debug mode

    Returns
    -------
    ker : ndarray
        2D array that represents kernel
    """
    rad = ker_params.ker_rad
    R = ker_params.ring_rad
    W = ker_params.ring_wid
    zetap = ker_params.zetap

    # Create grids
    xx, yy = np.meshgrid(np.arange(-rad, rad + 1), np.arange(-rad, rad + 1))

    # Calculate radius
    rr = np.sqrt(np.power(xx, 2) + np.power(yy, 2))

    # Calculate interim kernels
    ker1 = np.math.pi * np.math.pow(R, 2) * somb(2 * R * rr)
    ker2 = np.math.pi * np.math.pow(R - W, 2) * somb(2 * (R-W) * rr)

    kerr = ker1 - ker2
    keri = (zetap * np.math.cos(angle) - np.math.sin(angle)) * kerr

    ker = keri
    ker[rad + 0, rad + 0] = ker[rad + 0, rad + 0] + np.math.sin(angle)

    # normalize kernel
    ker = ker / np.linalg.norm(ker, 2)

    if debug:
        # Display kernel
        imgs = [(ker, 'Kernel:')]
        dbg.save_debug_fig(imgs, 'ker.png')

    return ker


def validate_params(ker_params, opt_params):
    """ Validates input parameters """
    return validate_ker_params(ker_params) and validate_opt_params(opt_params)


def validate_ker_params(ker_params):
    """ Validates kernel parameters """

    valid = True
    if ker_params.ring_rad <= 0:
        print("Error! Phase ring radius (kernel parameter) must be greater than zero")
        valid = False
    if ker_params.ring_wid <= 0:
        print("Error! Phase ring width (kernel parameter) must be greater than zero")
        valid = False
    if ker_params.ker_rad <= 0:
        print("Error! Kernel radius (kernel parameter) must be greater than zero")
        valid = False
    if ker_params.zetap <= 0:
        print("Error! Zetap (kernel parameter) must be greater than zero")
        valid = False
    if ker_params.dict_size <= 0:
        print("Error! Dictionary size (kernel parameter) must be greater than zero")
        valid = False

    return valid


def validate_opt_params(opt_params):
    """ Validates optimization parameters """
    valid = True
    if opt_params.smooth_weight <= 0:
        print("Error! Spatial smoothness weight (optimization parameter) must be greater than zero")
        valid = False
    if opt_params.spars_weight <= 0:
        print("Error! Sparsity term weight (optimization parameter) must be greater than zero")
        valid = False
    if opt_params.sel_basis <= 0:
        print("Error! Max selected basis (optimization parameter) must be greater than zero")
        valid = False
    if opt_params.epsilon <= 0:
        print("Error! Epsilon (optimization parameter) must be greater than zero")
        valid = False
    if opt_params.gamma <= 0:
        print("Error! Gamma (optimization parameter) must be greater than zero")
        valid = False
    if opt_params.img_scale <= 0:
        print("Error! Image scaling factor (optimization parameter) must be greater than zero")
        valid = False
    if opt_params.max_itr <= 0:
        print("Error! Max iterations (optimization parameter) must be greater than zero")
        valid = False
    if opt_params.opt_tolr <= 0:
        print("Error! Optimization tolerance (optimization parameter) must be greater than zero")
        valid = False

    return valid


def basis_select(img, ker_params, M, debug = False):
    """

    Selects best basis

    Parameters
    ----------
    img : ndarray
        2D array that represents image

    ker_params : KerParams
        kernal parameters

    M : ndarray
        TODO

    debug : bool
        is in debug mode

    Returns
    -------
        TODO
    """

    # get image dimensions
    rows_no = np.size(img, 0)
    cols_no = np.size(img, 1)
    N = cols_no * rows_no

    innerNorm = np.empty(M)
    imgs = []
    for m in range(1, M):
        angle = 2 * np.pi / M * m
        kernel = get_kernel(ker_params, angle, debug)
        basis = calc_basis(kernel, rows_no, cols_no)

        res_feature = np.dot(basis, img.flatten(order='F'))
        res_feature = np.reshape(res_feature, (rows_no, cols_no))

        # nullify negative elements
        res_feature[res_feature < 3] = 0

        res_feature_flat = res_feature.flatten(order='F')

        innerNorm[m] = np.linalg.norm(res_feature_flat)

        if debug:
            imgs += [(imtil.normalize(res_feature), 'Inner Production of basis with phase retardation' + str(m) + 'times 2*pi' )]

    if debug:
        dbg.save_debug_fig(imgs, 'basis_select.png')

    return innerNorm.argmax()


def somb(mat):
    """

    Returns a matrix whose elements are the somb of mat's elements

    Author(s) of original method: J. Loomis, 6-29-1999

    Parameters
    ----------
    mat : ndarray
        Matrix

    Returns
    -------
        Matrix whose elements are somb of mat's elements -
        y = 2*j1(pi*x)/(pi*x)    if x != 0
        1                       if x == 0
    """
    mat = np.abs(mat)
    nzero_idx = np.nonzero(mat) # find indices of non-zero elements in mat
    smb = np.zeros(mat.shape)
    smb[nzero_idx] = 2.0 * scipy.special.jn(1, np.pi * mat[nzero_idx]) / (np.pi * mat[nzero_idx]) # calc somb

    return smb


def phase_seg(basis, img, opt_params, debug = False):
    # Initialize
    w_smooth_spatio = opt_params.smooth_weight
    w_sparsity = opt_params.spars_weight
    epsilon = opt_params.epsilon
    gamma = opt_params.gamma
    m_scale = opt_params.img_scale
    maxiter = opt_params.max_itr
    tol = opt_params.opt_tolr

    # Create kernel
    (nrows, ncols) = img.shape
    N = nrows * ncols
    H = basis
    H = H.dot(H.conj())

    # Calculate spatial smoothness term



def calc_basis(kernel, nrows, ncols):
    '''

    :param kernel:
    :param nrows:
    :param ncols:
    :return:
    '''

    diameter = np.size(kernel, 1)
    radius = round((diameter - 1) / 2.0)
    kernel = kernel.flatten(order='F')
    N = nrows * ncols

    # build sparse matrix H
    logic_arr = (abs(kernel) > 0.01)
    logic_arr = np.array([int(x) for x in logic_arr])

    inds = np.reshape(np.arange(1, N+1), (nrows, ncols), order='F')

    inds_pad = np.pad(inds, np.array([radius, radius]), mode='symmetric')

    row_inds = np.tile(np.arange(1, N+1), (sum(logic_arr), 1))
    row_inds = row_inds.flatten(order='F')
    col_inds = im2col_sliding_strided(inds_pad.T, (diameter, diameter))

    logic_arr_col = logic_arr[:, None]
    filter_mat = np.tile(logic_arr_col, (1,N))
    col_inds = np.array([col_inds[i,j] for j in range(np.size(filter_mat, 1))
                                       for i in range(np.size(filter_mat, 0))
                                       if filter_mat[i,j] == 1])
    row_inds -= 1
    col_inds -= 1
    vals = np.tile(kernel[np.nonzero(logic_arr)], (1, N)).flatten()
    basis = sparse.csr_matrix((vals, (row_inds, col_inds)), shape=(N,N))

    return basis


def im2col_sliding_strided(A, BSZ, stepsize=1):
    # Parameters
    m,n = A.shape
    s0, s1 = A.strides
    nrows = m-BSZ[0]+1
    ncols = n-BSZ[1]+1
    shp = BSZ[0],BSZ[1],nrows,ncols
    strd = s0,s1,s0,s1

    out_view = np.lib.stride_tricks.as_strided(A, shape=shp, strides=strd)
    return out_view.reshape(BSZ[0]*BSZ[1],-1)[:,::stepsize]


if __name__ == "__main__":
    kernel = np.array([[2,1,0], [0, 1, 0], [0, 0, 1]])
    calc_basis(kernel, 3, 3)
