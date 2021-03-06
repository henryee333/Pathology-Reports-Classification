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
"""List maintenance policy command."""
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.calliope import base


class List(base.ListCommand):
  """List Google Compute Engine maintenance policies."""

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat("""\
        table(
          name,
          description,
          region,
          creationTimestamp
        )""")
    # TODO(b/69426858): Remove these deprecated flags.
    lister.AddRegionsArg(parser, hidden=True)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    request_data = lister.ParseRegionalFlags(args, holder.resources)

    list_implementation = lister.RegionalLister(
        client, client.apitools_client.maintenancePolicies)

    return lister.Invoke(request_data, list_implementation)


List.detailed_help = base_classes.GetRegionalListerHelp('maintenance policies')
