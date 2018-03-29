"""
Test ndarray subclass that handles symbolic units.




"""

# ----------------------------------------------------------------------------
# Copyright (c) 2013, yt Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# ----------------------------------------------------------------------------

import copy
from six.moves import cPickle as pickle
import itertools
import numpy as np
import operator
import os
import shutil
import tempfile

from distutils.version import LooseVersion
from nose.tools import assert_true
from numpy.testing import (
    assert_array_equal,
    assert_equal, assert_raises,
    assert_array_almost_equal_nulp,
    assert_array_almost_equal,
    assert_almost_equal
)
from numpy import array
from unyt.array import (
    unyt_array,
    unyt_quantity,
    unary_operators,
    binary_operators,
    uconcatenate,
    uintersect1d,
    uunion1d,
    loadtxt,
    savetxt
)
from unyt.exceptions import (
    UnitOperationError,
    UfuncUnitError
)
from unyt.testing import assert_allclose_units
from unyt.unit_symbols import (
    cm,
    m,
    g,
    degree
)
from unyt.unit_registry import UnitRegistry
from unyt.on_demand_imports import (
    _astropy,
    _pint
)
from unyt.physical_ratios import (
    metallicity_sun,
    speed_of_light_cm_per_s
)
from unyt import dimensions


def operate_and_compare(a, b, op, answer):
    # Test generator for unyt_arrays tests
    assert_array_equal(op(a, b), answer)


def assert_isinstance(a, type):
    assert isinstance(a, type)


def test_addition():
    """
    Test addition of two unyt_arrays

    """

    # Same units
    a1 = unyt_array([1, 2, 3], 'cm')
    a2 = unyt_array([4, 5, 6], 'cm')
    a3 = [4*cm, 5*cm, 6*cm]
    answer = unyt_array([5, 7, 9], 'cm')

    operate_and_compare(a1, a2, operator.add, answer)
    operate_and_compare(a2, a1, operator.add, answer)
    operate_and_compare(a1, a3, operator.add, answer)
    operate_and_compare(a3, a1, operator.add, answer)
    operate_and_compare(a2, a1, np.add, answer)
    operate_and_compare(a1, a2, np.add, answer)
    operate_and_compare(a1, a3, np.add, answer)
    operate_and_compare(a3, a1, np.add, answer)

    # different units
    a1 = unyt_array([1, 2, 3], 'cm')
    a2 = unyt_array([4, 5, 6], 'm')
    a3 = [4*m, 5*m, 6*m]
    answer1 = unyt_array([401, 502, 603], 'cm')
    answer2 = unyt_array([4.01, 5.02, 6.03], 'm')

    operate_and_compare(a1, a2, operator.add, answer1)
    operate_and_compare(a2, a1, operator.add, answer2)
    operate_and_compare(a1, a3, operator.add, answer1)
    if LooseVersion(np.__version__) < LooseVersion('1.13.0'):
        operate_and_compare(a3, a1, operator.add, answer1)
        assert_raises(UfuncUnitError, np.add, a1, a2)
        assert_raises(UfuncUnitError, np.add, a1, a3)
    else:
        operate_and_compare(a3, a1, operator.add, answer2)
        operate_and_compare(a1, a2, np.add, answer1)
        operate_and_compare(a2, a1, np.add, answer2)
        operate_and_compare(a1, a3, np.add, answer1)
        operate_and_compare(a3, a1, np.add, answer2)

    # Test dimensionless quantities
    a1 = unyt_array([1, 2, 3])
    a2 = array([4, 5, 6])
    a3 = [4, 5, 6]
    answer = unyt_array([5, 7, 9])

    operate_and_compare(a1, a2, operator.add, answer)
    operate_and_compare(a2, a1, operator.add, answer)
    operate_and_compare(a1, a3, operator.add, answer)
    operate_and_compare(a3, a1, operator.add, answer)
    operate_and_compare(a1, a2, np.add, answer)
    operate_and_compare(a2, a1, np.add, answer)
    operate_and_compare(a1, a3, np.add, answer)
    operate_and_compare(a3, a1, np.add, answer)

    # Catch the different dimensions error
    a1 = unyt_array([1, 2, 3], 'm')
    a2 = unyt_array([4, 5, 6], 'kg')
    a3 = [7, 8, 9]
    a4 = unyt_array([10, 11, 12], '')

    assert_raises(UnitOperationError, operator.add, a1, a2)
    assert_raises(UnitOperationError, operator.iadd, a1, a2)
    assert_raises(UnitOperationError, operator.add, a1, a3)
    assert_raises(UnitOperationError, operator.iadd, a1, a3)
    assert_raises(UnitOperationError, operator.add, a3, a1)
    assert_raises(UnitOperationError, operator.iadd, a3, a1)
    assert_raises(UnitOperationError, operator.add, a1, a4)
    assert_raises(UnitOperationError, operator.iadd, a1, a4)
    assert_raises(UnitOperationError, operator.add, a4, a1)
    assert_raises(UnitOperationError, operator.iadd, a4, a1)

    # adding with zero is allowed irrespective of the units
    zeros = np.zeros(3)
    zeros_yta_dimless = unyt_array(zeros, 'dimensionless')
    zeros_yta_length = unyt_array(zeros, 'm')
    zeros_yta_mass = unyt_array(zeros, 'kg')
    operands = [0, unyt_quantity(0), unyt_quantity(0, 'kg'), zeros,
                zeros_yta_dimless, zeros_yta_length, zeros_yta_mass]

    for op in [operator.add, np.add]:
        for operand in operands:
            operate_and_compare(a1, operand, op, a1)
            operate_and_compare(operand, a1, op, a1)
            operate_and_compare(4*m, operand, op, 4*m)
            operate_and_compare(operand, 4*m, op, 4*m)


def test_subtraction():
    """
    Test subtraction of two unyt_arrays

    """

    # Same units
    a1 = unyt_array([1, 2, 3], 'cm')
    a2 = unyt_array([4, 5, 6], 'cm')
    a3 = [4*cm, 5*cm, 6*cm]
    answer1 = unyt_array([-3, -3, -3], 'cm')
    answer2 = unyt_array([3, 3, 3], 'cm')

    operate_and_compare(a1, a2, operator.sub, answer1)
    operate_and_compare(a2, a1, operator.sub, answer2)
    operate_and_compare(a1, a3, operator.sub, answer1)
    operate_and_compare(a3, a1, operator.sub, answer2)
    operate_and_compare(a1, a2, np.subtract, answer1)
    operate_and_compare(a2, a1, np.subtract, answer2)
    operate_and_compare(a1, a3, np.subtract, answer1)
    operate_and_compare(a3, a1, np.subtract, answer2)

    # different units
    a1 = unyt_array([1, 2, 3], 'cm')
    a2 = unyt_array([4, 5, 6], 'm')
    a3 = [4*m, 5*m, 6*m]
    answer1 = unyt_array([-399, -498, -597], 'cm')
    answer2 = unyt_array([3.99, 4.98, 5.97], 'm')
    answer3 = unyt_array([399, 498, 597], 'cm')

    operate_and_compare(a1, a2, operator.sub, answer1)
    operate_and_compare(a2, a1, operator.sub, answer2)
    operate_and_compare(a1, a3, operator.sub, answer1)
    operate_and_compare(a3, a1, operator.sub, answer3)
    if LooseVersion(np.__version__) < LooseVersion('1.13.0'):
        assert_raises(UfuncUnitError, np.subtract, a1, a2)
        assert_raises(UfuncUnitError, np.subtract, a1, a3)
    else:
        operate_and_compare(a1, a2, np.subtract, answer1)
        operate_and_compare(a2, a1, np.subtract, answer2)
        operate_and_compare(a1, a3, np.subtract, answer1)
        operate_and_compare(a3, a1, np.subtract, answer3)

    # Test dimensionless quantities
    a1 = unyt_array([1, 2, 3])
    a2 = array([4, 5, 6])
    a3 = [4, 5, 6]
    answer1 = unyt_array([-3, -3, -3])
    answer2 = unyt_array([3, 3, 3])

    operate_and_compare(a1, a2, operator.sub, answer1)
    operate_and_compare(a2, a1, operator.sub, answer2)
    operate_and_compare(a1, a3, operator.sub, answer1)
    operate_and_compare(a3, a1, operator.sub, answer2)
    operate_and_compare(a1, a2, np.subtract, answer1)
    operate_and_compare(a2, a1, np.subtract, answer2)
    operate_and_compare(a1, a3, np.subtract, answer1)
    operate_and_compare(a3, a1, np.subtract, answer2)

    # Catch the different dimensions error
    a1 = unyt_array([1, 2, 3], 'm')
    a2 = unyt_array([4, 5, 6], 'kg')
    a3 = [7, 8, 9]
    a4 = unyt_array([10, 11, 12], '')

    assert_raises(UnitOperationError, operator.sub, a1, a2)
    assert_raises(UnitOperationError, operator.isub, a1, a2)
    assert_raises(UnitOperationError, operator.sub, a1, a3)
    assert_raises(UnitOperationError, operator.isub, a1, a3)
    assert_raises(UnitOperationError, operator.sub, a3, a1)
    assert_raises(UnitOperationError, operator.isub, a3, a1)
    assert_raises(UnitOperationError, operator.sub, a1, a4)
    assert_raises(UnitOperationError, operator.isub, a1, a4)
    assert_raises(UnitOperationError, operator.sub, a4, a1)
    assert_raises(UnitOperationError, operator.isub, a4, a1)

    # subtracting with zero is allowed irrespective of the units
    zeros = np.zeros(3)
    zeros_yta_dimless = unyt_array(zeros, 'dimensionless')
    zeros_yta_length = unyt_array(zeros, 'm')
    zeros_yta_mass = unyt_array(zeros, 'kg')
    operands = [0, unyt_quantity(0), unyt_quantity(0, 'kg'), zeros,
                zeros_yta_dimless, zeros_yta_length, zeros_yta_mass]

    for op in [operator.sub, np.subtract]:
        for operand in operands:
            operate_and_compare(a1, operand, op, a1)
            operate_and_compare(operand, a1, op, -a1)
            operate_and_compare(4*m, operand, op, 4*m)
            operate_and_compare(operand, 4*m, op, -4*m)


def test_multiplication():
    """
    Test multiplication of two unyt_arrays

    """

    # Same units
    a1 = unyt_array([1, 2, 3], 'cm')
    a2 = unyt_array([4, 5, 6], 'cm')
    a3 = [4*cm, 5*cm, 6*cm]
    answer = unyt_array([4, 10, 18], 'cm**2')

    operate_and_compare(a1, a2, operator.mul, answer)
    operate_and_compare(a2, a1, operator.mul, answer)
    operate_and_compare(a1, a3, operator.mul, answer)
    operate_and_compare(a3, a1, operator.mul, answer)
    operate_and_compare(a1, a2, np.multiply, answer)
    operate_and_compare(a2, a1, np.multiply, answer)
    operate_and_compare(a1, a3, np.multiply, answer)
    operate_and_compare(a3, a1, np.multiply, answer)

    # different units, same dimension
    a1 = unyt_array([1, 2, 3], 'cm')
    a2 = unyt_array([4, 5, 6], 'm')
    a3 = [4*m, 5*m, 6*m]
    answer1 = unyt_array([400, 1000, 1800], 'cm**2')
    answer2 = unyt_array([.04, .10, .18], 'm**2')
    answer3 = unyt_array([4, 10, 18], 'cm*m')

    operate_and_compare(a1, a2, operator.mul, answer1)
    operate_and_compare(a2, a1, operator.mul, answer2)
    operate_and_compare(a1, a3, operator.mul, answer1)
    operate_and_compare(a3, a1, operator.mul, answer2)
    operate_and_compare(a1, a2, np.multiply, answer3)
    operate_and_compare(a2, a1, np.multiply, answer3)
    operate_and_compare(a1, a3, np.multiply, answer3)
    operate_and_compare(a3, a1, np.multiply, answer3)

    # different dimensions
    a1 = unyt_array([1, 2, 3], 'cm')
    a2 = unyt_array([4, 5, 6], 'g')
    a3 = [4*g, 5*g, 6*g]
    answer = unyt_array([4, 10, 18], 'cm*g')

    operate_and_compare(a1, a2, operator.mul, answer)
    operate_and_compare(a2, a1, operator.mul, answer)
    operate_and_compare(a1, a3, operator.mul, answer)
    operate_and_compare(a3, a1, operator.mul, answer)
    operate_and_compare(a1, a2, np.multiply, answer)
    operate_and_compare(a2, a1, np.multiply, answer)
    operate_and_compare(a1, a3, np.multiply, answer)
    operate_and_compare(a3, a1, np.multiply, answer)

    # One dimensionless, one unitful
    a1 = unyt_array([1, 2, 3], 'cm')
    a2 = array([4, 5, 6])
    a3 = [4, 5, 6]
    answer = unyt_array([4, 10, 18], 'cm')

    operate_and_compare(a1, a2, operator.mul, answer)
    operate_and_compare(a2, a1, operator.mul, answer)
    operate_and_compare(a1, a3, operator.mul, answer)
    operate_and_compare(a3, a1, operator.mul, answer)
    operate_and_compare(a1, a2, np.multiply, answer)
    operate_and_compare(a2, a1, np.multiply, answer)
    operate_and_compare(a1, a3, np.multiply, answer)
    operate_and_compare(a3, a1, np.multiply, answer)

    # Both dimensionless quantities
    a1 = unyt_array([1, 2, 3])
    a2 = array([4, 5, 6])
    a3 = [4, 5, 6]
    answer = unyt_array([4, 10, 18])

    operate_and_compare(a1, a2, operator.mul, answer)
    operate_and_compare(a2, a1, operator.mul, answer)
    operate_and_compare(a1, a3, operator.mul, answer)
    operate_and_compare(a3, a1, operator.mul, answer)
    operate_and_compare(a1, a2, np.multiply, answer)
    operate_and_compare(a2, a1, np.multiply, answer)
    operate_and_compare(a1, a3, np.multiply, answer)
    operate_and_compare(a3, a1, np.multiply, answer)


def test_division():
    """
    Test multiplication of two unyt_arrays

    """

    # Same units
    a1 = unyt_array([1., 2., 3.], 'cm')
    a2 = unyt_array([4., 5., 6.], 'cm')
    a3 = [4*cm, 5*cm, 6*cm]
    answer1 = unyt_array([0.25, 0.4, 0.5])
    answer2 = unyt_array([4, 2.5, 2])
    if "div" in dir(operator):
        op = operator.div
    else:
        op = operator.truediv

    operate_and_compare(a1, a2, op, answer1)
    operate_and_compare(a2, a1, op, answer2)
    operate_and_compare(a1, a3, op, answer1)
    operate_and_compare(a3, a1, op, answer2)
    operate_and_compare(a1, a2, np.divide, answer1)
    operate_and_compare(a2, a1, np.divide, answer2)
    operate_and_compare(a1, a3, np.divide, answer1)
    operate_and_compare(a3, a1, np.divide, answer2)

    # different units, same dimension
    a1 = unyt_array([1., 2., 3.], 'cm')
    a2 = unyt_array([4., 5., 6.], 'm')
    a3 = [4*m, 5*m, 6*m]
    answer1 = unyt_array([.0025, .004, .005])
    answer2 = unyt_array([400, 250, 200])
    answer3 = unyt_array([0.25, 0.4, 0.5], 'cm/m')
    answer4 = unyt_array([4.0, 2.5, 2.0], 'm/cm')

    operate_and_compare(a1, a2, op, answer1)
    operate_and_compare(a2, a1, op, answer2)
    operate_and_compare(a1, a3, op, answer1)
    operate_and_compare(a3, a1, op, answer2)
    if LooseVersion(np.__version__) < LooseVersion('1.13.0'):
        operate_and_compare(a1, a2, np.divide, answer3)
        operate_and_compare(a2, a1, np.divide, answer4)
        operate_and_compare(a1, a3, np.divide, answer3)
        operate_and_compare(a3, a1, np.divide, answer4)
    else:
        operate_and_compare(a1, a2, np.divide, answer1)
        operate_and_compare(a2, a1, np.divide, answer2)
        operate_and_compare(a1, a3, np.divide, answer1)
        operate_and_compare(a3, a1, np.divide, answer2)

    # different dimensions
    a1 = unyt_array([1., 2., 3.], 'cm')
    a2 = unyt_array([4., 5., 6.], 'g')
    a3 = [4*g, 5*g, 6*g]
    answer1 = unyt_array([0.25, 0.4, 0.5], 'cm/g')
    answer2 = unyt_array([4, 2.5, 2], 'g/cm')

    operate_and_compare(a1, a2, op, answer1)
    operate_and_compare(a2, a1, op, answer2)
    operate_and_compare(a1, a3, op, answer1)
    operate_and_compare(a3, a1, op, answer2)
    operate_and_compare(a1, a2, np.divide, answer1)
    operate_and_compare(a2, a1, np.divide, answer2)
    operate_and_compare(a1, a3, np.divide, answer1)
    operate_and_compare(a3, a1, np.divide, answer2)

    # One dimensionless, one unitful
    a1 = unyt_array([1., 2., 3.], 'cm')
    a2 = array([4., 5., 6.])
    a3 = [4, 5, 6]
    answer1 = unyt_array([0.25, 0.4, 0.5], 'cm')
    answer2 = unyt_array([4, 2.5, 2], '1/cm')

    operate_and_compare(a1, a2, op, answer1)
    operate_and_compare(a2, a1, op, answer2)
    operate_and_compare(a1, a3, op, answer1)
    operate_and_compare(a3, a1, op, answer2)
    operate_and_compare(a1, a2, np.divide, answer1)
    operate_and_compare(a2, a1, np.divide, answer2)
    operate_and_compare(a1, a3, np.divide, answer1)
    operate_and_compare(a3, a1, np.divide, answer2)

    # Both dimensionless quantities
    a1 = unyt_array([1., 2., 3.])
    a2 = array([4., 5., 6.])
    a3 = [4, 5, 6]
    answer1 = unyt_array([0.25, 0.4, 0.5])
    answer2 = unyt_array([4, 2.5, 2])

    operate_and_compare(a1, a2, op, answer1)
    operate_and_compare(a2, a1, op, answer2)
    operate_and_compare(a1, a3, op, answer1)
    operate_and_compare(a3, a1, op, answer2)
    operate_and_compare(a1, a3, np.divide, answer1)
    operate_and_compare(a3, a1, np.divide, answer2)
    operate_and_compare(a1, a3, np.divide, answer1)
    operate_and_compare(a3, a1, np.divide, answer2)


def test_power():
    """
    Test power operator ensure units are correct.

    """

    from unyt import cm

    cm_arr = np.array([1.0, 1.0]) * cm

    assert_equal(cm**3, unyt_quantity(1, 'cm**3'))
    assert_equal(np.power(cm, 3), unyt_quantity(1, 'cm**3'))
    assert_equal(cm**unyt_quantity(3), unyt_quantity(1, 'cm**3'))
    assert_raises(UnitOperationError, np.power, cm, unyt_quantity(3, 'g'))

    assert_equal(cm_arr**3, unyt_array([1, 1], 'cm**3'))
    assert_equal(np.power(cm_arr, 3), unyt_array([1, 1], 'cm**3'))
    assert_equal(cm_arr**unyt_quantity(3), unyt_array([1, 1], 'cm**3'))
    assert_raises(UnitOperationError, np.power, cm_arr,
                  unyt_quantity(3, 'g'))


def test_comparisons():
    """
    Test numpy ufunc comparison operators for unit consistency.

    """
    from unyt.array import unyt_array

    a1 = unyt_array([1, 2, 3], 'cm')
    a2 = unyt_array([2, 1, 3], 'cm')
    a3 = unyt_array([.02, .01, .03], 'm')
    dimless = np.array([2, 1, 3])

    ops = (
        np.less,
        np.less_equal,
        np.greater,
        np.greater_equal,
        np.equal,
        np.not_equal
    )

    answers = (
        [True, False, False],
        [True, False, True],
        [False, True, False],
        [False, True, True],
        [False, False, True],
        [True, True, False],
    )

    for op, answer in zip(ops, answers):
        operate_and_compare(a1, a2, op, answer)
    for op, answer in zip(ops, answers):
        operate_and_compare(a1, dimless, op, answer)

    for op, answer in zip(ops, answers):
        if LooseVersion(np.__version__) < LooseVersion('1.13.0'):
            assert_raises(UfuncUnitError, op, a1, a3)
        else:
            operate_and_compare(a1, a3, op, answer)

    for op, answer in zip(ops, answers):
        operate_and_compare(a1, a3.in_units('cm'), op, answer)

    # Check that comparisons with dimensionless quantities work in both
    # directions.
    operate_and_compare(a3, dimless, np.less, [True, True, True])
    operate_and_compare(dimless, a3, np.less, [False, False, False])
    assert_equal(a1 < 2, [True, False, False])
    assert_equal(a1 < 2, np.less(a1, 2))
    assert_equal(2 < a1, [False, False, True])
    assert_equal(2 < a1, np.less(2, a1))


def test_unit_conversions():
    """
    Test operations that convert to different units or cast to ndarray

    """
    from unyt.array import unyt_quantity
    from unyt.unit_object import Unit

    km = unyt_quantity(1, 'km')
    km_in_cm = km.in_units('cm')
    cm_unit = Unit('cm')
    kpc_unit = Unit('kpc')

    assert_equal(km_in_cm, km)
    assert_equal(km_in_cm.in_cgs(), 1e5)
    assert_equal(km_in_cm.in_mks(), 1e3)
    assert_equal(km_in_cm.units, cm_unit)

    km_view = km.ndarray_view()
    km.convert_to_units('cm')
    assert_true(km_view.base is km.base)

    assert_equal(km, unyt_quantity(1, 'km'))
    assert_equal(km.in_cgs(), 1e5)
    assert_equal(km.in_mks(), 1e3)
    assert_equal(km.units, cm_unit)

    km.convert_to_units('kpc')
    assert_true(km_view.base is km.base)

    assert_array_almost_equal_nulp(km, unyt_quantity(1, 'km'))
    assert_array_almost_equal_nulp(km.in_cgs(), unyt_quantity(1e5, 'cm'))
    assert_array_almost_equal_nulp(km.in_mks(), unyt_quantity(1e3, 'm'))
    assert_equal(km.units, kpc_unit)

    assert_isinstance(km.to_ndarray(), np.ndarray)
    assert_isinstance(km.ndarray_view(), np.ndarray)

    dyne = unyt_quantity(1.0, 'dyne')

    assert_equal(dyne.in_cgs(), dyne)
    assert_equal(dyne.in_cgs(), 1.0)
    assert_equal(dyne.in_mks(), dyne)
    assert_equal(dyne.in_mks(), 1e-5)
    assert_equal(str(dyne.in_mks().units), 'kg*m/s**2')
    assert_equal(str(dyne.in_cgs().units), 'cm*g/s**2')

    em3 = unyt_quantity(1.0, 'erg/m**3')

    assert_equal(em3.in_cgs(), em3)
    assert_equal(em3.in_cgs(), 1e-6)
    assert_equal(em3.in_mks(), em3)
    assert_equal(em3.in_mks(), 1e-7)
    assert_equal(str(em3.in_mks().units), 'kg/(m*s**2)')
    assert_equal(str(em3.in_cgs().units), 'g/(cm*s**2)')

    em3_converted = unyt_quantity(1545436840.386756, 'Msun/(Myr**2*kpc)')
    assert_equal(em3.in_base(unit_system="galactic"), em3)
    assert_array_almost_equal(
        em3.in_base(unit_system="galactic"), em3_converted)
    assert_equal(
        str(em3.in_base(unit_system="galactic").units), 'Msun/(Myr**2*kpc)')

    dimless = unyt_quantity(1.0, "")
    assert_equal(dimless.in_cgs(), dimless)
    assert_equal(dimless.in_cgs(), 1.0)
    assert_equal(dimless.in_mks(), dimless)
    assert_equal(dimless.in_mks(), 1.0)
    assert_equal(str(dimless.in_cgs().units), "dimensionless")


def test_temperature_conversions():
    """
    Test conversions between various supported temperatue scales.

    Also ensure we only allow compound units with temperature
    scales that have a proper zero point.

    """
    from unyt.unit_object import InvalidUnitOperation

    km = unyt_quantity(1, 'km')
    balmy = unyt_quantity(300, 'K')
    balmy_F = unyt_quantity(80.33, 'degF')
    balmy_C = unyt_quantity(26.85, 'degC')
    balmy_R = unyt_quantity(540, 'R')

    assert_array_almost_equal(balmy.in_units('degF'), balmy_F)
    assert_array_almost_equal(balmy.in_units('degC'), balmy_C)
    assert_array_almost_equal(balmy.in_units('R'), balmy_R)

    balmy_view = balmy.ndarray_view()

    balmy.convert_to_units('degF')
    assert_true(balmy_view.base is balmy.base)
    assert_array_almost_equal(np.array(balmy), np.array(balmy_F))

    balmy.convert_to_units('degC')
    assert_true(balmy_view.base is balmy.base)
    assert_array_almost_equal(np.array(balmy), np.array(balmy_C))

    balmy.convert_to_units('R')
    assert_true(balmy_view.base is balmy.base)
    assert_array_almost_equal(np.array(balmy), np.array(balmy_R))

    balmy.convert_to_units('degF')
    assert_true(balmy_view.base is balmy.base)
    assert_array_almost_equal(np.array(balmy), np.array(balmy_F))

    assert_raises(InvalidUnitOperation, np.multiply, balmy, km)

    # Does CGS conversion from F to K work?
    assert_array_almost_equal(balmy.in_cgs(), unyt_quantity(300, 'K'))


def test_unyt_array_unyt_quantity_ops():
    """
    Test operations that combine unyt_array and unyt_quantity
    """
    a = unyt_array(range(10, 1), 'cm')
    b = unyt_quantity(5, 'g')

    assert_isinstance(a*b, unyt_array)
    assert_isinstance(b*a, unyt_array)

    assert_isinstance(a/b, unyt_array)
    assert_isinstance(b/a, unyt_array)

    assert_isinstance(a*a, unyt_array)
    assert_isinstance(a/a, unyt_array)

    assert_isinstance(b*b, unyt_quantity)
    assert_isinstance(b/b, unyt_quantity)


def test_selecting():
    """
    Test slicing of two unyt_arrays

    """
    a = unyt_array(range(10), 'cm')
    a_slice = a[:3]
    a_fancy_index = a[[1, 1, 3, 5]]
    a_array_fancy_index = a[array([[1, 1], [3, 5]])]
    a_boolean_index = a[a > 5]
    a_selection = a[0]

    assert_array_equal(a_slice, unyt_array([0, 1, 2], 'cm'))
    assert_equal(a_slice.units, a.units)
    assert_array_equal(a_fancy_index, unyt_array([1, 1, 3, 5], 'cm'))
    assert_equal(a_fancy_index.units, a.units)
    assert_array_equal(a_array_fancy_index,
                       unyt_array([[1, 1, ], [3, 5]], 'cm'))
    assert_equal(a_array_fancy_index.units, a.units)
    assert_array_equal(a_boolean_index, unyt_array([6, 7, 8, 9], 'cm'))
    assert_equal(a_boolean_index.units, a.units)
    assert_isinstance(a_selection, unyt_quantity)
    assert_equal(a_selection.units, a.units)

    # .base points to the original array for a numpy view.  If it is not a
    # view, .base is None.
    assert_true(a_slice.base is a)


def test_iteration():
    """
    Test that iterating over a unyt_array returns a sequence of unyt_quantity
    instances
    """
    a = np.arange(3)
    b = unyt_array(np.arange(3), 'cm')
    for ia, ib, in zip(a, b):
        assert_equal(ia, ib.value)
        assert_equal(ib.units, b.units)


def test_ytarray_pickle():
    test_data = [unyt_quantity(12.0, 'cm'),
                 unyt_array([1, 2, 3], 'km')]

    for data in test_data:
        tempf = tempfile.NamedTemporaryFile(delete=False)
        pickle.dump(data, tempf)
        tempf.close()

        with open(tempf.name, "rb") as fname:
            loaded_data = pickle.load(fname)
        os.unlink(tempf.name)

        assert_array_equal(data, loaded_data)
        assert_equal(data.units, loaded_data.units)
        assert_array_equal(array(data.in_cgs()), array(loaded_data.in_cgs()))
        assert_equal(float(data.units.base_value),
                     float(loaded_data.units.base_value))


def test_copy():
    quan = unyt_quantity(1, 'g')
    arr = unyt_array([1, 2, 3], 'cm')

    assert_equal(copy.copy(quan), quan)
    assert_array_equal(copy.copy(arr), arr)

    assert_equal(copy.deepcopy(quan), quan)
    assert_array_equal(copy.deepcopy(arr), arr)

    assert_equal(quan.copy(), quan)
    assert_array_equal(arr.copy(), arr)

    assert_equal(np.copy(quan), quan)
    assert_array_equal(np.copy(arr), arr)


# needed so the tests function on older numpy versions that have
# different sets of ufuncs
def yield_np_ufuncs(ufunc_list):
    for u in ufunc_list:
        ufunc = getattr(np, u, None)
        if ufunc is not None:
            yield ufunc


def unary_ufunc_comparison(ufunc, a):
    out = a.copy()
    a_array = a.to_ndarray()
    if ufunc in (np.isreal, np.iscomplex, ):
        # According to the numpy docs, these two explicitly do not do
        # in-place copies.
        ret = ufunc(a)
        assert_true(not hasattr(ret, 'units'))
        assert_array_equal(ret, ufunc(a))
    elif ufunc in yield_np_ufuncs([
            'exp', 'exp2', 'log', 'log2', 'log10', 'expm1', 'log1p', 'sin',
            'cos', 'tan', 'arcsin', 'arccos', 'arctan', 'sinh', 'cosh', 'tanh',
            'arccosh', 'arcsinh', 'arctanh', 'deg2rad', 'rad2deg', 'isfinite',
            'isinf', 'isnan', 'signbit', 'sign', 'rint', 'logical_not']):
        # These operations should return identical results compared to numpy.
        with np.errstate(invalid='ignore'):
            try:
                ret = ufunc(a, out=out)
            except UnitOperationError:
                assert_true(ufunc in (np.deg2rad, np.rad2deg))
                ret = ufunc(unyt_array(a, '1'))

            assert_array_equal(ret, out)
            assert_array_equal(ret, ufunc(a_array))
            # In-place copies do not drop units.
            assert_true(hasattr(out, 'units'))
            assert_true(not hasattr(ret, 'units'))
    elif ufunc in yield_np_ufuncs(
            ['absolute', 'fabs', 'conjugate', 'floor', 'ceil', 'trunc',
             'negative', 'spacing', 'positive']):

        ret = ufunc(a, out=out)

        assert_array_equal(ret, out)
        assert_array_equal(ret.to_ndarray(), ufunc(a_array))
        assert_true(ret.units == out.units)
    elif ufunc in yield_np_ufuncs(
            ['ones_like', 'square', 'sqrt', 'reciprocal']):
        if ufunc is np.ones_like:
            ret = ufunc(a)
        else:
            with np.errstate(invalid='ignore'):
                ret = ufunc(a, out=out)
            assert_array_equal(ret, out)

        with np.errstate(invalid='ignore'):
            assert_array_equal(ret.to_ndarray(), ufunc(a_array))
        if ufunc is np.square:
            assert_true(out.units == a.units**2)
            assert_true(ret.units == a.units**2)
        elif ufunc is np.sqrt:
            assert_true(out.units == a.units**0.5)
            assert_true(ret.units == a.units**0.5)
        elif ufunc is np.reciprocal:
            assert_true(out.units == a.units**-1)
            assert_true(ret.units == a.units**-1)
    elif ufunc is np.modf:
        ret1, ret2 = ufunc(a)
        npret1, npret2 = ufunc(a_array)

        assert_array_equal(ret1.to_ndarray(), npret1)
        assert_array_equal(ret2.to_ndarray(), npret2)
    elif ufunc is np.frexp:
        ret1, ret2 = ufunc(a)
        npret1, npret2 = ufunc(a_array)

        assert_array_equal(ret1, npret1)
        assert_array_equal(ret2, npret2)
    elif ufunc is np.invert:
        assert_raises(TypeError, ufunc, a)
    elif hasattr(np, 'isnat') and ufunc is np.isnat:
        # numpy 1.13 raises ValueError, numpy 1.14 and newer raise TypeError
        assert_raises((TypeError, ValueError), ufunc, a)
    else:
        # There shouldn't be any untested ufuncs.
        assert_true(False)


def binary_ufunc_comparison(ufunc, a, b):
    out = a.copy()
    if ufunc in yield_np_ufuncs([
            'add', 'subtract', 'remainder', 'fmod', 'mod', 'arctan2', 'hypot',
            'greater', 'greater_equal', 'less', 'less_equal', 'equal',
            'not_equal', 'logical_and', 'logical_or', 'logical_xor', 'maximum',
            'minimum', 'fmax', 'fmin', 'nextafter', 'heaviside']):
        if a.units != b.units and a.units.dimensions == b.units.dimensions:
            if LooseVersion(np.__version__) < LooseVersion('1.13.0'):
                assert_raises(UfuncUnitError, ufunc, a, b)
                return
        elif a.units != b.units:
            assert_raises(UnitOperationError, ufunc, a, b)
            return
    if ufunc in yield_np_ufuncs(
            ['bitwise_and', 'bitwise_or', 'bitwise_xor', 'left_shift',
             'right_shift', 'ldexp']):
        assert_raises(TypeError, ufunc, a, b)
        return

    ret = ufunc(a, b, out=out)
    ret = ufunc(a, b)

    if ufunc is np.multiply:
        assert_true(ret.units == a.units*b.units)
    elif ufunc in (np.divide, np.true_divide, np.arctan2):
        assert_true(ret.units.dimensions == (a.units/b.units).dimensions)
    elif ufunc in (np.greater, np.greater_equal, np.less, np.less_equal,
                   np.not_equal, np.equal, np.logical_and, np.logical_or,
                   np.logical_xor):
        assert_true(not isinstance(ret, unyt_array) and
                    isinstance(ret, np.ndarray))
    if isinstance(ret, tuple):
        assert_array_equal(ret[0], out)
    else:
        assert_array_equal(ret, out)
    if ((ufunc in (np.divide, np.true_divide, np.arctan2) and
         (a.units.dimensions == b.units.dimensions))):
        assert_array_almost_equal(
            np.array(ret), ufunc(np.array(a.in_cgs()), np.array(b.in_cgs())))
    elif LooseVersion(np.__version__) < LooseVersion('1.13.0'):
        assert_array_almost_equal(np.array(ret),
                                  ufunc(np.array(a), np.array(b)))


def test_ufuncs():
    for ufunc in unary_operators:
        if ufunc is None:
            continue
        unary_ufunc_comparison(ufunc, unyt_array([.3, .4, .5], 'cm'))
        unary_ufunc_comparison(ufunc, unyt_array([12, 23, 47], 'g'))
        unary_ufunc_comparison(ufunc, unyt_array([2, 4, -6], 'erg/m**3'))

    for ufunc in binary_operators:
        if ufunc is None:
            continue
        # arr**arr is undefined for arrays with units because
        # each element of the result would have different units.
        if ufunc is np.power:
            a = unyt_array([.3, .4, .5], 'cm')
            b = unyt_array([.1, .2, .3], 'dimensionless')
            c = np.array(b)
            d = unyt_array([1., 2., 3.], 'g')
            assert_raises(UnitOperationError, ufunc, a, b)
            assert_raises(UnitOperationError, ufunc, a, c)
            assert_raises(UnitOperationError, ufunc, a, d)
            continue

        a = unyt_array([.3, .4, .5], 'cm')
        b = unyt_array([.1, .2, .3], 'cm')
        c = unyt_array([.1, .2, .3], 'm')
        d = unyt_array([.1, .2, .3], 'g')
        e = unyt_array([.1, .2, .3], 'erg/m**3')

        for pair in itertools.product([a, b, c, d, e], repeat=2):
            binary_ufunc_comparison(ufunc, pair[0], pair[1])


def test_reductions():
    arr = unyt_array([[1, 2, 3], [4, 5, 6]], 'cm')

    ev_result = arr.dot(unyt_array([1, 2, 3], 'cm'))
    res = unyt_array([14., 32.], 'cm**2')
    assert_equal(ev_result, res)
    assert_equal(ev_result.units, res.units)
    assert_isinstance(ev_result, unyt_array)

    answers = {
        'prod': (unyt_quantity(720, 'cm**6'),
                 unyt_array([4, 10, 18], 'cm**2'),
                 unyt_array([6, 120], 'cm**3')),
        'sum': (unyt_quantity(21, 'cm'),
                unyt_array([5., 7., 9.], 'cm'),
                unyt_array([6, 15], 'cm'),),
        'mean': (unyt_quantity(3.5, 'cm'),
                 unyt_array([2.5, 3.5, 4.5], 'cm'),
                 unyt_array([2, 5], 'cm')),
        'std': (unyt_quantity(1.707825127659933, 'cm'),
                unyt_array([1.5, 1.5, 1.5], 'cm'),
                unyt_array([0.81649658, 0.81649658], 'cm')),
    }
    for op, (result1, result2, result3) in answers.items():
        ev_result = getattr(arr, op)()
        assert_almost_equal(ev_result, result1)
        assert_almost_equal(ev_result.units, result1.units)
        assert_isinstance(ev_result, unyt_quantity)
        for axis, result in [(0, result2), (1, result3), (-1, result3)]:
            ev_result = getattr(arr, op)(axis=axis)
            assert_almost_equal(ev_result, result)
            assert_almost_equal(ev_result.units, result.units)
            assert_isinstance(ev_result, unyt_array)


def test_convenience():

    arr = unyt_array([1, 2, 3], 'cm')

    assert_equal(arr.unit_quantity, unyt_quantity(1, 'cm'))
    assert_equal(arr.uq, unyt_quantity(1, 'cm'))
    assert_isinstance(arr.unit_quantity, unyt_quantity)
    assert_isinstance(arr.uq, unyt_quantity)

    assert_array_equal(arr.unit_array, unyt_array(np.ones_like(arr), 'cm'))
    assert_array_equal(arr.ua, unyt_array(np.ones_like(arr), 'cm'))
    assert_isinstance(arr.unit_array, unyt_array)
    assert_isinstance(arr.ua, unyt_array)

    assert_array_equal(arr.ndview, arr.view(np.ndarray))
    assert_array_equal(arr.d, arr.view(np.ndarray))
    assert_true(arr.ndview.base is arr.base)
    assert_true(arr.d.base is arr.base)

    assert_array_equal(arr.value, np.array(arr))
    assert_array_equal(arr.v, np.array(arr))


def test_registry_association():
    reg = UnitRegistry()
    a = unyt_quantity(3, 'cm', registry=reg)
    b = unyt_quantity(4, 'm')
    c = unyt_quantity(6, '', registry=reg)
    d = 5

    assert_equal(id(a.units.registry), id(reg))

    def binary_op_registry_comparison(op):
        e = op(a, b)
        f = op(b, a)
        g = op(c, d)
        h = op(d, c)

        assert_equal(id(e.units.registry), id(reg))
        assert_equal(id(f.units.registry), id(b.units.registry))
        assert_equal(id(g.units.registry), id(h.units.registry))
        assert_equal(id(g.units.registry), id(reg))

    def unary_op_registry_comparison(op):
        c = op(a)
        d = op(b)

        assert_equal(id(c.units.registry), id(reg))
        assert_equal(id(d.units.registry), id(b.units.registry))

    binary_ops = [operator.add, operator.sub, operator.mul,
                  operator.truediv]
    if hasattr(operator, "div"):
        binary_ops.append(operator.div)
    for op in binary_ops:
        binary_op_registry_comparison(op)

    for op in [operator.abs, operator.neg, operator.pos]:
        unary_op_registry_comparison(op)


def test_to_value():

    a = unyt_array([1.0, 2.0, 3.0], "kpc")
    assert_equal(a.to_value(), np.array([1.0, 2.0, 3.0]))
    assert_equal(a.to_value(), a.value)
    assert_equal(a.to_value("km"), a.in_units("km").value)

    b = unyt_quantity(5.5, "Msun")
    assert_equal(b.to_value(), 5.5)
    assert_equal(b.to_value("g"), b.in_units("g").value)


def test_astropy():
    ap_arr = np.arange(10)*_astropy.units.km/_astropy.units.hr
    yt_arr = unyt_array(np.arange(10), "km/hr")
    yt_arr2 = unyt_array.from_astropy(ap_arr)

    ap_quan = 10.*_astropy.units.Msun**0.5/(_astropy.units.kpc**3)
    yt_quan = unyt_quantity(10., "sqrt(Msun)/kpc**3")
    yt_quan2 = unyt_quantity.from_astropy(ap_quan)

    assert_array_equal(ap_arr, yt_arr.to_astropy())
    assert_array_equal(yt_arr, unyt_array.from_astropy(ap_arr))
    assert_array_equal(yt_arr, yt_arr2)

    assert_equal(ap_quan, yt_quan.to_astropy())
    assert_equal(yt_quan, unyt_quantity.from_astropy(ap_quan))
    assert_equal(yt_quan, yt_quan2)

    assert_array_equal(yt_arr, unyt_array.from_astropy(yt_arr.to_astropy()))
    assert_equal(yt_quan, unyt_quantity.from_astropy(yt_quan.to_astropy()))


def test_pint():
    ureg = _pint.UnitRegistry()

    p_arr = np.arange(10)*ureg.km/ureg.hr
    yt_arr = unyt_array(np.arange(10), "km/hr")
    yt_arr2 = unyt_array.from_pint(p_arr)

    p_quan = 10.*ureg.g**0.5/(ureg.mm**3)
    yt_quan = unyt_quantity(10., "sqrt(g)/mm**3")
    yt_quan2 = unyt_quantity.from_pint(p_quan)

    assert_array_equal(p_arr, yt_arr.to_pint())
    assert_equal(p_quan, yt_quan.to_pint())
    assert_array_equal(yt_arr, unyt_array.from_pint(p_arr))
    assert_array_equal(yt_arr, yt_arr2)

    assert_equal(p_quan.magnitude, yt_quan.to_pint().magnitude)
    assert_equal(p_quan, yt_quan.to_pint())
    assert_equal(yt_quan, unyt_quantity.from_pint(p_quan))
    assert_equal(yt_quan, yt_quan2)

    assert_array_equal(yt_arr, unyt_array.from_pint(yt_arr.to_pint()))
    assert_equal(yt_quan, unyt_quantity.from_pint(yt_quan.to_pint()))


def test_subclass():

    class unyt_a_subclass(unyt_array):
        pass

    a = unyt_a_subclass([4, 5, 6], 'g')
    b = unyt_a_subclass([7, 8, 9], 'kg')
    nu = unyt_a_subclass([10, 11, 12], '')
    nda = np.array([3, 4, 5])
    yta = unyt_array([6, 7, 8], 'mg')
    loq = [unyt_quantity(6, 'mg'), unyt_quantity(7, 'mg'),
           unyt_quantity(8, 'mg')]
    ytq = unyt_quantity(4, 'cm')
    ndf = np.float64(3)

    def op_comparison(op, inst1, inst2, compare_class):
        assert_isinstance(op(inst1, inst2), compare_class)
        assert_isinstance(op(inst2, inst1), compare_class)

    ops = [operator.mul, operator.truediv]
    if hasattr(operator, "div"):
        ops.append(operator.div)
    for op in ops:
        for inst in (b, ytq, ndf, yta, nda, loq):
            op_comparison(op, a, inst, unyt_a_subclass)

        op_comparison(op, ytq, nda, unyt_array)
        op_comparison(op, ytq, yta, unyt_array)

    for op in (operator.add, operator.sub):
        op_comparison(op, nu, nda, unyt_a_subclass)
        op_comparison(op, a, b, unyt_a_subclass)
        op_comparison(op, a, yta, unyt_a_subclass)
        op_comparison(op, a, loq, unyt_a_subclass)

    assert_isinstance(a[0], unyt_quantity)
    assert_isinstance(a[:], unyt_a_subclass)
    assert_isinstance(a[:2], unyt_a_subclass)
    assert_isinstance(unyt_a_subclass(yta), unyt_a_subclass)


def test_h5_io():
    tmpdir = tempfile.mkdtemp()
    curdir = os.getcwd()
    os.chdir(tmpdir)

    reg = UnitRegistry()

    reg.add('code_length', 10.0, dimensions.length)

    warr = unyt_array(np.random.random((256, 256)), 'code_length',
                      registry=reg)

    warr.write_hdf5('test.h5')

    iarr = unyt_array.from_hdf5('test.h5')

    assert_equal(warr, iarr)
    assert_equal(warr.units.registry['code_length'],
                 iarr.units.registry['code_length'])

    warr.write_hdf5('test.h5', dataset_name="test_dset",
                    group_name='/arrays/test_group')

    giarr = unyt_array.from_hdf5('test.h5', dataset_name="test_dset",
                                 group_name='/arrays/test_group')

    assert_equal(warr, giarr)

    os.chdir(curdir)
    shutil.rmtree(tmpdir)


def test_equivalencies():
    import unyt as u

    # Mass-energy

    E = u.mp.in_units("keV", "mass_energy")
    assert_equal(E, u.mp*u.clight*u.clight)
    assert_allclose_units(u.mp, E.in_units("g", "mass_energy"))

    # Thermal

    T = unyt_quantity(1.0e8, "K")
    E = T.in_units("W*hr", "thermal")
    assert_equal(E, (u.kboltz*T).in_units("W*hr"))
    assert_allclose_units(T, E.in_units("K", "thermal"))

    # Spectral

    length = unyt_quantity(4000., "angstrom")
    nu = length.in_units("Hz", "spectral")
    assert_equal(nu, u.clight/length)
    E = u.hcgs*nu
    l2 = E.in_units("angstrom", "spectral")
    assert_allclose_units(length, l2)
    nu2 = u.clight/l2.in_units("cm")
    assert_allclose_units(nu, nu2)
    E2 = nu2.in_units("keV", "spectral")
    assert_allclose_units(E2, E.in_units("keV"))

    # Sound-speed

    mu = 0.6
    gg = 5./3.
    c_s = T.in_units("km/s", equivalence="sound_speed")
    assert_equal(c_s, np.sqrt(gg*u.kboltz*T/(mu*u.mh)))
    assert_allclose_units(T, c_s.in_units("K", "sound_speed"))

    mu = 0.5
    gg = 4./3.
    c_s = T.in_units("km/s", "sound_speed", mu=mu, gamma=gg)
    assert_equal(c_s, np.sqrt(gg*u.kboltz*T/(mu*u.mh)))
    assert_allclose_units(T, c_s.in_units("K", "sound_speed", mu=mu, gamma=gg))

    # Lorentz

    v = 0.8*u.clight
    g = v.in_units("dimensionless", "lorentz")
    g2 = unyt_quantity(1./np.sqrt(1.-0.8*0.8), "dimensionless")
    assert_allclose_units(g, g2)
    v2 = g2.in_units("mile/hr", "lorentz")
    assert_allclose_units(v2, v.in_units("mile/hr"))

    # Schwarzschild

    R = u.mass_sun_cgs.in_units("kpc", "schwarzschild")
    assert_equal(R.in_cgs(), 2*u.G*u.mass_sun_cgs/(u.clight**2))
    assert_allclose_units(u.mass_sun_cgs, R.in_units("g", "schwarzschild"))

    # Compton

    length = u.me.in_units("angstrom", "compton")
    assert_equal(length, u.hcgs/(u.me*u.clight))
    assert_allclose_units(u.me, length.in_units("g", "compton"))

    # Number density

    rho = u.mp/u.cm**3

    n = rho.in_units("cm**-3", "number_density")
    assert_equal(n, rho/(u.mh*0.6))
    assert_allclose_units(rho, n.in_units("g/cm**3", "number_density"))

    n = rho.in_units("cm**-3", equivalence="number_density", mu=0.75)
    assert_equal(n, rho/(u.mh*0.75))
    assert_allclose_units(
        rho, n.in_units("g/cm**3", equivalence="number_density", mu=0.75))

    # Effective temperature

    T = unyt_quantity(1.0e4, "K")
    F = T.in_units("erg/s/cm**2", equivalence="effective_temperature")
    assert_equal(F, u.stefan_boltzmann_constant_cgs*T**4)
    assert_allclose_units(
        T, F.in_units("K", equivalence="effective_temperature"))

    # to_value test

    assert_equal(
        F.value,
        T.to_value("erg/s/cm**2", equivalence="effective_temperature"))
    assert_equal(
        n.value,
        rho.to_value("cm**-3", equivalence="number_density", mu=0.75))


def test_electromagnetic():
    import unyt as u

    # Various tests of SI and CGS electromagnetic units

    qp_mks = u.qp.in_units("C", "SI")
    assert_equal(qp_mks.units.dimensions, dimensions.charge_mks)
    assert_array_almost_equal(qp_mks.v, 10.0*u.qp.v/speed_of_light_cm_per_s)

    qp_cgs = qp_mks.in_units("esu", "CGS")
    assert_array_almost_equal(qp_cgs, u.qp)
    assert_equal(qp_cgs.units.dimensions, u.qp.units.dimensions)

    qp_mks_k = u.qp.in_units("kC", "SI")
    assert_array_almost_equal(
        qp_mks_k.v, 1.0e-2*u.qp.v/speed_of_light_cm_per_s)

    B = unyt_quantity(1.0, "T")
    B_cgs = B.in_units("gauss", "CGS")
    assert_equal(B.units.dimensions, dimensions.magnetic_field_mks)
    assert_equal(B_cgs.units.dimensions, dimensions.magnetic_field_cgs)
    assert_array_almost_equal(B_cgs, unyt_quantity(1.0e4, "gauss"))

    u_mks = B*B/(2*u.mu_0)
    assert_equal(u_mks.units.dimensions, dimensions.pressure)
    u_cgs = B_cgs*B_cgs/(8*np.pi)
    assert_equal(u_cgs.units.dimensions, dimensions.pressure)
    assert_array_almost_equal(u_mks.in_cgs(), u_cgs)

    current = unyt_quantity(1.0, "A")
    I_cgs = current.in_units("statA", equivalence="CGS")
    assert_array_almost_equal(
        I_cgs, unyt_quantity(0.1*speed_of_light_cm_per_s, "statA"))
    assert_array_almost_equal(
        I_cgs.in_units("mA", equivalence="SI"), current.in_units("mA"))
    assert_equal(I_cgs.units.dimensions, dimensions.current_cgs)

    R = unyt_quantity(1.0, "ohm")
    R_cgs = R.in_units("statohm", "CGS")
    P_mks = current*current*R
    P_cgs = I_cgs*I_cgs*R_cgs
    assert_equal(P_mks.units.dimensions, dimensions.power)
    assert_equal(P_cgs.units.dimensions, dimensions.power)
    assert_array_almost_equal(P_cgs.in_cgs(), P_mks.in_cgs())
    assert_array_almost_equal(P_cgs.in_mks(), unyt_quantity(1.0, "W"))

    V = unyt_quantity(1.0, "statV")
    V_mks = V.in_units("V", "SI")
    assert_array_almost_equal(V_mks.v, 1.0e8*V.v/speed_of_light_cm_per_s)


def test_ytarray_coercion():
    a = unyt_array([1, 2, 3], 'cm')
    q = unyt_quantity(3, 'cm')
    na = np.array([1, 2, 3])

    assert_isinstance(a*q, unyt_array)
    assert_isinstance(q*na, unyt_array)
    assert_isinstance(q*3, unyt_quantity)
    assert_isinstance(q*np.float64(3), unyt_quantity)
    assert_isinstance(q*np.array(3), unyt_quantity)


def test_numpy_wrappers():
    a1 = unyt_array([1, 2, 3], 'cm')
    a2 = unyt_array([2, 3, 4, 5, 6], 'cm')
    catenate_answer = [1, 2, 3, 2, 3, 4, 5, 6]
    intersect_answer = [2, 3]
    union_answer = [1, 2, 3, 4, 5, 6]

    assert_array_equal(unyt_array(catenate_answer, 'cm'),
                       uconcatenate((a1, a2)))
    assert_array_equal(catenate_answer, np.concatenate((a1, a2)))

    assert_array_equal(unyt_array(intersect_answer, 'cm'),
                       uintersect1d(a1, a2))
    assert_array_equal(intersect_answer, np.intersect1d(a1, a2))

    assert_array_equal(unyt_array(union_answer, 'cm'), uunion1d(a1, a2))
    assert_array_equal(union_answer, np.union1d(a1, a2))


def test_dimensionless_conversion():
    a = unyt_quantity(1, 'Zsun')
    b = a.in_units('Zsun')
    a.convert_to_units('Zsun')
    assert_true(a.units.base_value == metallicity_sun)
    assert_true(b.units.base_value == metallicity_sun)


def test_modified_unit_division():
    reg1 = UnitRegistry()
    reg2 = UnitRegistry()

    # this mocks comoving coordinates without going through the trouble
    # of setting up a fake cosmological dataset
    reg1.modify('m', 50)

    a = unyt_quantity(3, 'm', registry=reg1)
    b = unyt_quantity(3, 'm', registry=reg2)

    ret = a/b
    assert_true(ret == 0.5)
    assert_true(ret.units.is_dimensionless)
    assert_true(ret.units.base_value == 1.0)


def test_load_and_save():
    tmpdir = tempfile.mkdtemp()
    curdir = os.getcwd()
    os.chdir(tmpdir)

    a = unyt_array(np.random.random(10), "kpc")
    b = unyt_array(np.random.random(10), "Msun")
    c = unyt_array(np.random.random(10), "km/s")

    savetxt("arrays.dat", [a, b, c], delimiter=",")

    d, e = loadtxt("arrays.dat", usecols=(1, 2), delimiter=",")

    assert_array_equal(b, d)
    assert_array_equal(c, e)

    os.chdir(curdir)
    shutil.rmtree(tmpdir)


def test_trig_ufunc_degrees():
    for ufunc in (np.sin, np.cos, np.tan):
        degree_values = np.random.random(10)*degree
        radian_values = degree_values.in_units('radian')
        assert_array_equal(ufunc(degree_values), ufunc(radian_values))


def test_builtin_sum():
    from unyt import km

    arr = [1, 2, 3]*km
    assert_equal(sum(arr), 6*km)


def test_initialization_different_registries():

    reg1 = UnitRegistry()
    reg2 = UnitRegistry()

    reg1.add('code_length', 1.0, dimensions.length)
    reg2.add('code_length', 3.0, dimensions.length)

    l1 = unyt_quantity(1.0, 'code_length', registry=reg1)
    l2 = unyt_quantity(1.0, 'code_length', registry=reg2)

    assert_almost_equal(float(l1.in_cgs()), 1.0)
    assert_almost_equal(float(l2.in_cgs()), 3.0)


def test_ones_and_zeros_like():
    data = unyt_array([1, 2, 3], 'cm')
    zd = np.zeros_like(data)
    od = np.ones_like(data)

    assert_equal(zd, unyt_array([0, 0, 0], 'cm'))
    assert_equal(zd.units, data.units)
    assert_equal(od, unyt_array([1, 1, 1], 'cm'))
    assert_equal(od.units, data.units)