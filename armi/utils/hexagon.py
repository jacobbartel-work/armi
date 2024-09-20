# Copyright 2019 TerraPower, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

r"""
Generic hexagon math.

Hexagons are fundamental to advanced reactors.

.. image:: /.static/hexagon.png
    :width: 100%
"""

import math
import typing

import numpy as np

from armi.utils import iterables

SQRT3 = math.sqrt(3.0)


def area(pitch):
    """
    Area of a hex given the flat-to-flat pitch.

    .. impl:: Compute hexagonal area
        :id: I_ARMI_UTIL_HEXAGON0
        :implements: R_ARMI_UTIL_HEXAGON

        Computes the area of a hexagon given the flat-to-flat ``pitch``.

    Notes
    -----
    The pitch is the distance between the center of the hexagons in the lattice.
    """
    return SQRT3 / 2.0 * pitch**2


def side(pitch):
    r"""
    Side length of a hex given the flat-to-flat pitch.

    Pythagorean theorem says:

    .. math::

        \frac{s}{2}^2 + \frac{p}{2}^2 = s^2

    which you can solve to find p = sqrt(3)*s

    Notes
    -----
    The pitch is the distance between the center of the hexagons in the lattice.
    """
    return pitch / SQRT3


def corners(rotation=0):
    """
    Return the coordinates of a unit hexagon, rotated as requested.

    Zero rotation implies flat-to-flat aligned with y-axis. Origin in the center.
    """
    points = np.array(
        [
            (1.0 / (2.0 * math.sqrt(3.0)), 0.5),
            (1.0 / math.sqrt(3.0), 0.0),
            (1.0 / (2.0 * math.sqrt(3.0)), -0.5),
            (-1.0 / (2.0 * math.sqrt(3.0)), -0.5),
            (-1.0 / math.sqrt(3.0), 0.0),
            (-1.0 / (2.0 * math.sqrt(3.0)), 0.5),
        ]
    )

    rotation = rotation / 180.0 * math.pi

    rotation = np.array(
        [
            [math.cos(rotation), -math.sin(rotation)],
            [math.sin(rotation), math.cos(rotation)],
        ]
    )

    return np.array([tuple(rotation.dot(point)) for point in points])


def pitch(side):
    """
    Calculate the pitch from the length of a hexagon side.

    Notes
    -----
    The pitch is the distance between the center of the hexagons in the lattice.
    """
    return side * SQRT3


def numRingsToHoldNumCells(numCells):
    """
    Determine the number of rings in a hexagonal grid with this many hex cells.
    If the number of pins don't fit exactly into any ring, returns the ring just large
    enough to fit them.

    Parameters
    ----------
    numCells : int
        The number of hex cells in a hex lattice

    Returns
    -------
    numRings : int
        Number of rings required to contain numCells items.

    Notes
    -----
    The first hex ring (center) holds 1 position. Each subsequent hex ring contains 6
    more positions than the last.  This method works by incrementing ring numbers until
    the number of items is reached or exceeded. It could easily be replaced by a lookup
    table if so desired.
    """
    if numCells == 0:
        return 0
    nPinRings = int(math.ceil(0.5 * (1 + math.sqrt(1 + 4 * (numCells - 1) // 3))))

    return nPinRings


def numPositionsInRing(ring):
    """Number of positions in ring (starting at 1) of a hex lattice.

    .. impl:: Compute number of positions in a ring of a hex lattice
        :id: I_ARMI_UTIL_HEXAGON1
        :implements: R_ARMI_UTIL_HEXAGON

        In a hexagonal lattice, calculate the number of positions in a given ``ring``. The number of
        rings is indexed to 1, i.e. the centermost position in the lattice is ``ring=1``.
    """
    return (ring - 1) * 6 if ring != 1 else 1


def totalPositionsUpToRing(ring: int) -> int:
    """Return the number of positions in a hexagon with a given number of rings."""
    return 1 + 3 * ring * (ring - 1)


def getIndexOfRotatedCell(initialCellIndex: int, orientationNumber: int) -> int:
    """Obtain a new cell number after placing a hexagon in a new orientation.

    Parameters
    ----------
    initialCellIndex : int
        Positive number for this cell's position in a hexagonal lattice.
    orientationNumber :
        Orientation in number of 60 degree, counter clockwise rotations. An orientation
        of zero means the first cell in each ring of a flags up hexagon is in the upper
        right corner.

    Returns
    -------
    int
        New cell number across the rotation

    Raises
    ------
    ValueError
        If ``initialCellIndex`` is not positive.
        If ``orientationNumber`` is less than zero or greater than five.
    """
    if orientationNumber < 0 or orientationNumber > 5:
        raise ValueError(
            f"Orientation number must be in [0:5], got {orientationNumber}"
        )
    if initialCellIndex > 1:
        if orientationNumber == 0:
            return initialCellIndex
        ring = numRingsToHoldNumCells(initialCellIndex)
        tot_pins = totalPositionsUpToRing(ring)
        newPinLocation = initialCellIndex + (ring - 1) * orientationNumber
        if newPinLocation > tot_pins:
            newPinLocation -= (ring - 1) * 6
        return newPinLocation
    elif initialCellIndex == 1:
        return initialCellIndex
    raise ValueError(f"Cell number must be positive, got {initialCellIndex}")


def rotateHexCellData(
    data: typing.Union[list, np.ndarray], cells: int, nRotations: int
) -> typing.Union[list, np.ndarray]:
    """Rotate data defined on a hexagonal lattice.

    Consider a hexagon with three rings of cells. Each cell has a corresponding data, say a scalar
    for its unique pin number. That hexagon is rotated 60 degrees counter clockwise. We need to update
    these data so that the pin number for the pin originally in ring 2, position 1 travels
    to where the pin ends up. The before and after pin numbers would look like::

            9   8   7             7   18  17
          10  2   1   18        8   1   6   16
        11  3   0   6   17 -> 9   2   0   5   15
          12  4   5   10        10  3   4   14
            13  14  15            11  12  13

    Parameters
    ----------
    data : list or numpy.ndarray
        Data such that ``data[0]`` reflects data at the center of the hexagon,
        ``data[1]`` is for ring 2, position 1, ``data[2]`` matches ring 2, position 2,
        and generally ``data[i]`` corresponds to the ``i``-th cell in the ARMI spiraling
        indexing scheme.
    cells : int
        Number of cells that should exist. This should match the number of cells
        in a full hexagon and should also equal the number of elements in the first
        dimension of ``data``, e.g., ``cells == np.shape(data)[0]``.
    nRotations : int
        Number of 60 degree counter clockwise rotations.

    Returns
    -------
    list or numpy.ndarray
        Data rotated accordingly. Matches the type of the initial ``data`` object so if a ``list``
        was provided, a ``list`` will be returned.

    Notes
    -----
    This assumes you have a full hexagon of data. No empty cells.

    """
    if not isinstance(data, (list, np.ndarray)):
        raise TypeError(f"{data=}")
    if np.size(data, axis=0) != cells:
        raise ValueError(f"{len(data)=} != {cells}")
    buffer = np.empty_like(data)
    buffer[0] = data[0]
    nRings = numRingsToHoldNumCells(cells)

    ringPosStart = 1
    for ring in range(2, nRings + 1):
        pinsPerRing = numPositionsInRing(ring)
        pinsPerEdge = pinsPerRing // 6
        ringPosEnd = ringPosStart + pinsPerRing
        window = slice(ringPosStart, ringPosEnd)
        ringData = data[window]
        rotatedRingData = iterables.pivot(ringData, -(nRotations * pinsPerEdge))
        buffer[window] = rotatedRingData
        ringPosStart = ringPosEnd
    if isinstance(data, np.ndarray):
        return buffer
    return buffer.tolist()
