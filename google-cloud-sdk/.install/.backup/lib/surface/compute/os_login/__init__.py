# Copyright 2017 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""The super-group for the oslogin CLI."""

from googlecloudsdk.calliope import base


DETAILED_HELP = {
    'DESCRIPTION': """\
        The gcloud oslogin command group lets you manage your Google
        OS Login profile. OS Login profiles can be used to store infomation
        such as Posix account information and SSH keys used for other Google
        Cloud Platform products such as Google Compute Engine.
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Oslogin(base.Group):
  """Create and manipulate Google Compute Engine OS Login resources."""
  detailed_help = DETAILED_HELP
