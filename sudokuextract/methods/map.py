#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
corners
==================

Created by: hbldh <henrik.blidh@nedomkull.com>
Created on: 2016-03-05, 13:09

"""

from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

import numpy as np
from skimage.filters import gaussian_filter

from dlxsudoku.sudoku import Sudoku
from dlxsudoku.exceptions import SudokuException

from sudokuextract.exceptions import SudokuExtractError
from sudokuextract.imgproc.blob import iter_blob_contours
from sudokuextract.imgproc import geometry
from sudokuextract.ml.predict import classify_sudoku
from sudokuextract.utils import predictions_to_suduko_string


def extraction_method_map(image, classifier, use_local_thresholding=False, apply_gaussian=False, n=5, force=False):
    for sudoku, subimage in _extraction_iterator_map(image, use_local_thresholding, apply_gaussian, n=n):
        try:
            pred_n_imgs = classify_sudoku(sudoku, classifier)
            preds = np.array([[pred_n_imgs[k][kk][0] for kk in range(9)] for k in range(9)])
            imgs = [[pred_n_imgs[k][kk][1] for kk in range(9)] for k in range(9)]

            if np.sum(preds > 0) >= 17 or force:
                try:
                    s = Sudoku(predictions_to_suduko_string(preds))
                    s.solve()
                except SudokuException:
                    if force:
                        return preds, imgs, subimage
                except Exception:
                    pass
                else:
                    return preds, imgs, subimage
        except Exception as e:
            pass
    raise SudokuExtractError("Corner Method could not extract any Sudoku from this image.")


def _extraction_iterator_map(image, use_local_thresholding=False, apply_gaussian=False, n=5):

    if apply_gaussian:
        img = gaussian_filter(image, (3.0, 3.0))
    else:
        img = image

    for edges in iter_blob_contours(img, n=n):
        try:
            warped_image = geometry.warp_image_by_interp_borders(edges, img)
            sudoku, bin_image = geometry.split_image_into_sudoku_pieces_adaptive_global(
                warped_image, otsu_local=use_local_thresholding, apply_gaussian=apply_gaussian)
        except SudokuExtractError as e:
            pass
        except Exception as e:
            # Try next blob
            raise
        else:
            yield sudoku, bin_image
