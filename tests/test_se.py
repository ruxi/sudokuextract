#!/usr/bin/env python
# -0- coding: utf-8 -0-
"""
test_images
==================

Created by: hbldh <henrik.blidh@nedomkull.com>
Created on: 2016-01-28, 20:54

"""

from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

import os
import sys

import pytest

try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen

from PIL import Image

from sudokuextract.extract import extract_sudoku, main
from sudokuextract.utils import predictions_to_suduko_string, download_image, load_image
from sudokuextract.ml import fit

try:
    _range = xrange
except NameError:
    _range = range


def _get_img(nbr=1):
    return Image.open(_get_img_path(nbr))


def _get_img_path(nbr=1):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'img{0}.jpg'.format(nbr))


def _get_parsed_img(nbr=1):
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'img{0}.txt'.format(nbr)), 'rt') as f:
        parsed_img = f.read().strip()
    return parsed_img


@pytest.fixture(scope="module")
def classifier():
    return fit.get_default_sudokuextract_classifier()


def _process_an_image(image, correct_sudoku):
    predictions, sudoku, subimage = extract_sudoku(image, classifier())
    parsed_sudoku = predictions_to_suduko_string(predictions)
    assert parsed_sudoku == correct_sudoku


def test_image_1_cmd_1(capsys):
    """Test Image 1 via command line tool."""
    sys.argv = ['parse-sudoku', '-p', _get_img_path(1)]
    main()
    out, err = capsys.readouterr()
    correct_sudoku = _get_parsed_img(1)
    assert out.strip() == correct_sudoku


def test_image_1_cmd_2(capsys):
    """Test Image 1 via command line tool."""
    sys.argv = ['parse-sudoku', '-p', _get_img_path(1), '--oneliner']
    main()
    out, err = capsys.readouterr()
    correct_sudoku = _get_parsed_img(1).replace('\n', '')
    assert out.strip() == correct_sudoku


def test_image_2_cmd_1(capsys):
    """Test Image 1 via command line tool."""
    sys.argv = ['parse-sudoku', '-p', _get_img_path(2)]
    main()
    out, err = capsys.readouterr()
    correct_sudoku = _get_parsed_img(2)
    assert out.strip() == correct_sudoku


def test_image_2_cmd_2(capsys):
    """Test Image 2 via command line tool."""
    sys.argv = ['parse-sudoku', '-p', _get_img_path(2), '--oneliner']
    main()
    out, err = capsys.readouterr()
    correct_sudoku = _get_parsed_img(2).replace('\n', '')
    assert out.strip() == correct_sudoku


def test_image_1_with_trained_classifier():
    image = _get_img(1)
    c = fit.KNeighborsClassifier(n_neighbors=5)
    c = fit.fit_sudokuextract_classifier(c)
    predictions, sudoku, subimage = extract_sudoku(image, c)
    parsed_sudoku = predictions_to_suduko_string(predictions)
    assert parsed_sudoku == _get_parsed_img(1)


def test_image_2_with_trained_classifier():
    image = _get_img(2)
    c = fit.KNeighborsClassifier(n_neighbors=10)
    c = fit.fit_combined_classifier(c)
    predictions, sudoku, subimage = extract_sudoku(image, c)
    parsed_sudoku = predictions_to_suduko_string(predictions)
    assert parsed_sudoku == _get_parsed_img(2)


def test_url_1_straight():
    url = "https://static-secure.guim.co.uk/sys-images/Guardian/Pix/pictures/2013/2/27/1361977880123/Sudoku2437easy.jpg"
    image = download_image(url)
    solution = ("041006029\n"
                "300790000\n"
                "009000308\n"
                "800604290\n"
                "070050060\n"
                "036108007\n"
                "403000900\n"
                "000032004\n"
                "650400730")
    _process_an_image(image, solution)


def test_url_1_via_commandline(capsys):
    url = "https://static-secure.guim.co.uk/sys-images/Guardian/Pix/pictures/2013/2/27/1361977880123/Sudoku2437easy.jpg"
    sys.argv = ['parse-sudoku', '-u', url]
    main()
    out, err = capsys.readouterr()
    solution = ("041006029\n"
                "300790000\n"
                "009000308\n"
                "800604290\n"
                "070050060\n"
                "036108007\n"
                "403000900\n"
                "000032004\n"
                "650400730")
    assert out.strip() == solution


### Parameterized tests


if os.environ.get('XANADOKU_API_TOKEN') is not None:
    import json
    _url = "https://xanadoku.herokuapp.com/getallsudokus/" + os.environ.get('XANADOKU_API_TOKEN')
    try:
        xanadoku_sudokus = json.loads(urlopen(_url).read().decode('utf-8')).get('sudokus')
    except:
        xanadoku_sudokus = []
else:
    xanadoku_sudokus = []


@pytest.mark.parametrize("sudoku_doc", xanadoku_sudokus)
def test_xanadoku_sudokus(sudoku_doc):
    if not sudoku_doc.get('verified'):
        assert True
    else:
        print(sudoku_doc.get('_id'))
        image = download_image(sudoku_doc.get('raw_image_url'))
        predictions, sudoku, subimage = extract_sudoku(image, classifier(), force=True)
        parsed_sudoku = predictions_to_suduko_string(predictions, oneliner=True)
        if parsed_sudoku != sudoku_doc.get('parsed_sudoku'):
            predictions, sudoku, subimage = extract_sudoku(image.rotate(-90), classifier(), force=True)
            parsed_sudoku = predictions_to_suduko_string(predictions, oneliner=True)
        assert parsed_sudoku == sudoku_doc.get('parsed_sudoku')


@pytest.yield_fixture(scope='module')
def se_data_tar_files():
    if os.environ.get("SUDOKUEXTRACT_TEST_DATA_URL") is not None:
        import tarfile
        import tempfile

        temp_dir = tempfile.mkdtemp()
        f = tarfile.open(fileobj=urlopen(os.environ.get("SUDOKUEXTRACT_TEST_DATA_URL")), mode='r|gz')
        f.extractall(temp_dir)

        pth, _, files = next(os.walk(temp_dir))
        files = list(set([os.path.splitext(f)[0] for f in files]))
        files = [os.path.join(pth, f) for f in files]

        return files
    elif os.environ.get("SUDOKUEXTRACT_TEST_DATA_PATH") is not None:
        import tarfile
        import tempfile

        temp_dir = tempfile.mkdtemp()
        f = tarfile.open(os.environ.get("SUDOKUEXTRACT_TEST_DATA_PATH"), 'r:gz')
        f.extractall(temp_dir)
        f.close()

        pth, _, files = next(os.walk(temp_dir))
        files = list(set([os.path.splitext(f)[0] for f in files]))
        files = [os.path.join(pth, f) for f in files]

        return files
    else:
        return []


@pytest.mark.parametrize("file_path_base", se_data_tar_files())
def test_se_tardata_sudokus(file_path_base):
    try:
        image_file_name = file_path_base + '.jpg'
        image = load_image(image_file_name)
    except:
        image_file_name = file_path_base + '.png'
        image = load_image(image_file_name)
    with open(file_path_base + '.txt', 'rt') as f:
        correct_parsing = f.read().strip()

    predictions, sudoku, subimage = extract_sudoku(image, classifier(), force=True)
    parsed_sudoku = predictions_to_suduko_string(predictions, oneliner=False)
    if parsed_sudoku != correct_parsing:
        predictions, sudoku, subimage = extract_sudoku(image.rotate(-90), classifier(), force=True)
        parsed_sudoku = predictions_to_suduko_string(predictions, oneliner=False)
    assert parsed_sudoku == correct_parsing


    try:
        os.remove(image_file_name)
        os.remove(file_path_base + '.txt')
        print("Deleted temporary test dir.")
        os.removedirs(os.path.dirname(file_path_base))
    except:
        pass
