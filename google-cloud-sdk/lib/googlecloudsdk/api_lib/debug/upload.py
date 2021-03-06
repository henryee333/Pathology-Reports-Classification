# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Support for uploading files to Cloud Source Repositories."""

from datetime import datetime
import os
import re
import uuid
from apitools.base.py import exceptions
from googlecloudsdk.api_lib.source import git
from googlecloudsdk.api_lib.source.repos import sourcerepo
from googlecloudsdk.core import properties

# The repo where uploads are stored.
UPLOAD_REPO_NAME = 'google-source-captures'

# The error message when the repository for uploads does not exist.
REPO_NOT_FOUND_ERROR = ("The repository '{0}' does not exist in the project "
                        "'{1}'. Please run the command 'gcloud source repos "
                        "create --project={1} {0}' to create the repository, "
                        "or specify a different project with the --project "
                        "flag. Note that usage of Cloud Source Repositories "
                        "may incur charges. See "
                        "https://cloud.google.com/source-repositories/pricing "
                        "for details.")

# Branch names need to be unique, but do not need to be predictable, and there
# is no reliable human-readable name for them. For that reason, we generate a
# uuid string as the primary branch name of an explicit upload.
# Since the string is arbitrary, however, we can include some useful
# information to distinguish it for display, so we use the current date and
# time as a prefix.
TIME_FORMAT = '%Y/%m/%d-%H.%M.%S'


def _GetNow():
  return datetime.utcnow()


def _GetUuid():
  return uuid.uuid4()


class UploadManager(object):
  """Provides methods for uploading files to Cloud Source Repositories."""

  # 256KiB, maximum file size to upload
  SIZE_THRESHOLD = 256 * 2**10

  def __init__(self, project_id=None):
    if not project_id:
      project_id = properties.VALUES.core.project.Get(required=True)
    self._project_id = project_id
    self._ignore_handler = git.GitIgnoreHandler()
    # Add a top-level ignore for the .git directory (the expression matches
    # the .git directory and any file contained in it).
    self._ignore_handler.AddIgnoreRules(
        '/', [(re.compile(r'^(.*/)?\.git(/.*)?'), True)])

  def Upload(self, branch, root_path):
    """Uploads files to a branch in Cloud Source Repositories.

    Args:
      branch: (string) The name of the branch to upload to. If empty, a
        name will be generated.
      root_path: (string) The path of a directory tree to upload.

    Returns:
      A dictionary containing various status information:
        'branch': The name of the branch.
        'source_contexts': One or more dictionaries compatible with the
          ExtendedSourceContext message, including one context pointing
          to the upload. This context will be the only one with the value
          'capture' for its 'category' label.
        'files_written': The number of files uploaded.
        'files_skipped': The number of files skipped.
        'size_written': The total number of bytes in all files uploaded.
    """
    if not sourcerepo.Source().GetRepo(sourcerepo.ParseRepo(UPLOAD_REPO_NAME)):
      raise exceptions.Error(
          REPO_NOT_FOUND_ERROR.format(UPLOAD_REPO_NAME, self._project_id))

    branch = branch or (_GetNow().strftime(TIME_FORMAT) + '.' + _GetUuid().hex)
    all_paths = [
        f for f in self._ignore_handler.GetFiles(os.path.abspath(root_path))
        if not os.path.islink(f)
    ]
    paths = [f for f in all_paths if os.path.getsize(f) <= self.SIZE_THRESHOLD]
    git.Git(self._project_id, UPLOAD_REPO_NAME).ForcePushFilesToBranch(
        branch, root_path, paths)

    source_context = {
        'context': {
            'cloudRepo': {
                'repoId': {
                    'projectRepoId': {
                        'projectId': self._project_id,
                        'repoName': UPLOAD_REPO_NAME
                    }
                },
                'revision': {
                    'aliasContext': {
                        'kind': 'MOVABLE',
                        'name': branch
                    }
                }
            }
        },
        'labels': {
            'category': 'capture'
        }
    }

    return {
        'branch': branch,
        'source_contexts': [source_context],
        'files_written': len(paths),
        'files_skipped': len(all_paths) - len(paths),
        'size_written': sum([os.path.getsize(f) for f in paths])
    }
