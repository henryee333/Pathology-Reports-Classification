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
"""Utility library for configuring docker credential helpers."""
import collections
import json

from distutils import version as distutils_version
from googlecloudsdk.core.docker import client_lib as client_utils
from googlecloudsdk.core.docker import constants
from googlecloudsdk.core.util import files

MIN_DOCKER_CONFIG_HELPER_VERSION = distutils_version.LooseVersion('1.13')
CREDENTIAL_HELPER_KEY = 'credHelpers'


class DockerConfigUpdateError(client_utils.DockerError):
  """Error thrown for issues updating Docker configuration file updates."""


class Configuration(object):
  """Full Docker configuration configuration file and related meta-data."""

  def __init__(self, config_data, version, path=None):
    self.version = distutils_version.LooseVersion(version)
    self.contents = config_data
    self.path = path

  def __eq__(self, other):
    return (self.version == other.version and
            self.contents == other.contents and
            self.path == other.path)

  @classmethod
  def FromJson(cls, json_string, version, path):
    """Build a Configuration object from a JSON string.

    Args:
      json_string: string, json content for Configuration
      version: string, Docker version of Configuration
      path: string, file path to Docker Configuation File

    Returns:
      a Configuration object
    """
    if not json_string or json_string.isspace():
      config_dict = {}
    else:
      config_dict = json.loads(json_string)
    return Configuration(config_dict, version, path)

  def ToJson(self):
    """Get this Configuration objects contents as a JSON string."""
    return json.dumps(self.contents, indent=2)

  def SupportsRegistryHelpers(self):
    """Retruns True if this Configuration supports Docker registry helpers."""
    return self.version >= MIN_DOCKER_CONFIG_HELPER_VERSION

  def GetRegisteredCredentialHelpers(self):
    """Returns credential helpers entry from the Docker config file.

    Returns:
      'credHelpers' entry if it is specified in the Docker configuration or
      empty dict if the config does not contain a 'credHelpers' key.

    """
    if self.contents and CREDENTIAL_HELPER_KEY in self.contents:
      return {CREDENTIAL_HELPER_KEY:
              self.contents[CREDENTIAL_HELPER_KEY]}

    return {}

  def RegisterCredentialHelpers(self, mappings_dict=None):
    """Adds Docker 'credHelpers' entry to this configuration.

    Adds Docker 'credHelpers' entry to this configuration and writes updated
    configuration to disk.

    Args:
      mappings_dict: The dict of 'credHelpers' mappings ({registry: handler})
      to add to the Docker configuration. If not set, use default values from
      GetOrderedCredentialHelperRegistries()

    Raises:
      ValueError: mappings are not a valid dict.
      DockerConfigUpdateError: Configuration does not support 'credHelpers'.
    """
    mappings_dict = mappings_dict or GetOrderedCredentialHelperRegistries()
    if not isinstance(mappings_dict, dict):
      raise ValueError('Invalid Docker credential helpers mappings {}'.format(
          mappings_dict))

    if not self.SupportsRegistryHelpers():
      raise DockerConfigUpdateError('Credential Helpers not supported for this '
                                    'Docker client version {}'.format(
                                        self.version))

    self.contents[CREDENTIAL_HELPER_KEY] = mappings_dict
    self.WriteToDisk()

  def WriteToDisk(self):
    """Writes Conifguration object to disk."""
    try:
      files.WriteFileAtomically(self.path, self.ToJson())
    except (TypeError, ValueError, OSError, IOError) as err:
      raise DockerConfigUpdateError('Error writing Docker configuration '
                                    'to disk: {}'.format(str(err)))

  # Defaulting to new config location since we know minimum version
  # for supporting credential helpers is > 1.7.
  @classmethod
  def ReadFromDisk(cls, path=None):
    """Reads configuration file and meta-data from default Docker location.

    Reads configuration file and meta-data from default Docker location. Returns
    a Configuration object containing the full contents of the configuration
    file, the configuration file path and Docker version.

    Args:
      path: string, path to look for the Docker config file. If empty will
      attempt to read from the new config location (default).

    Returns:
      A Configuration object

    Raises:
      ValueError: path or is_new_format are not set.
      InvalidDockerConfigError: config file could not be read as JSON.
    """
    path = path or client_utils.GetDockerConfigPath(True)[0]
    try:
      version = str(client_utils.GetDockerVersion())
      content = client_utils.ReadConfigurationFile(path)
    except (ValueError, client_utils.DockerError)  as err:
      raise client_utils.InvalidDockerConfigError(
          ('Docker configuration file [{}] could not be read as JSON: {}'
          ).format(path, str(err)))

    return cls(content, version, path)


def _SupportedRegistries():
  """Return list of gcloud credential helper supported Docker registires."""
  return constants.ALL_SUPPORTED_REGISTRIES


def GetOrderedCredentialHelperRegistries():
  """Returns ordered dict of Docker registry to gcloud helper mappings.

  Ensures that the order in which credential helper registry entries are
  processed is consistient.

  Returns:
   OrderedDict of Docker registry to gcloud helper mappings.
  """
  # Based on Docker credHelper docs this should work on Windows transparently
  # so we do not need to register .exe files seperately, see
  # https://docs.docker.com/engine/reference/commandline/login/#credential-helpers
  return collections.OrderedDict([
      (registry, 'gcloud')
      for registry in _SupportedRegistries()
  ])


def GetGcloudCredentialHelperConfig():
  """Gets the credHelpers Docker config entry for gcloud supported registries.

  Returns a Docker configuration JSON entry that will register gcloud as the
  credential helper for all Google supported Docker registries. If mappings_only
  is True, it will only return the registered credential helper mappings instead
  of the entire credHelpers entry.

  Returns:
    The config used to register gcloud as the credential helper for all
    supported Docker registries.
  """
  registered_helpers = GetOrderedCredentialHelperRegistries()

  return {CREDENTIAL_HELPER_KEY: registered_helpers}
