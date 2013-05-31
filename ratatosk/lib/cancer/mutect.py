# Copyright (c) 2013 Per Unneberg
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.
"""
Provide wrappers for `mutect <http://www.broadinstitute.org/cancer/cga/mutect>`_


Classes
-------
"""

import os
import luigi
import logging
import ratatosk.lib.files.input
from ratatosk.utils import rreplace, fullclassname
from ratatosk.job import JobTask, JavaJobRunner
from ratatosk.log import get_logger
import ratatosk.shell as shell

logger = get_logger()

class InputBamFile(ratatosk.lib.files.input.InputBamFile):
    pass

class MutectJobRunner(JavaJobRunner):
    @staticmethod
    def _get_main(job):
        return "-T {}".format(job.main())


class MutectJobTask(JobTask):
    exe_path = luigi.Parameter(default=os.getenv("MUTECT_HOME") if os.getenv("MUTECT_HOME") else os.curdir)
    executable = luigi.Parameter(default="muTect.jar")
    source_suffix = luigi.Parameter(default=".bam")
    target_suffix = luigi.Parameter(default=".bam")
    java_exe = luigi.Parameter(default="java")
    java_options = luigi.Parameter(default=("-Xmx2g",), description="Java options", is_list=True)
    parent_task = luigi.Parameter(default="ratatosk.lib.tools.gatk.InputBamFile")
    ref = luigi.Parameter(default=None)
    can_multi_thread = True

    def jar(self):
        return self.executable

    def exe(self):
        return self.jar()

    def java_opt(self):
        return list(self.java_options)

    def java(self):
        return self.java_exe

    def job_runner(self):
        return MutectJobRunner()

