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

"""
State parameter definitions for Material objects.

See Also
--------
:py:mod:`armi.reactor.parameters`
"""
from armi.reactor import parameters
from armi.reactor.parameters import ParamLocation


def getMaterialParameterDefinitions():
    """
    Define the state parameters available on a Material object.

    .. note:: These are not stored in the database.
    """
    pDefs = parameters.ParameterDefinitionCollection()

    with pDefs.createBuilder(location=ParamLocation.AVERAGE, saveToDB=False) as pb:

        pb.defParam("massFrac", units=None, description="mass fractions")

    return pDefs
