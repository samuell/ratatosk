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
Provide wrappers for `snpeff <http://snpeff.sourceforge.net/>`_


Classes
-------
"""

import os
import luigi
import logging
import ratatosk.lib.files.input
from ratatosk.utils import rreplace, fullclassname
from ratatosk.job import JobTask, JobWrapperTask
from ratatosk.jobrunner import  DefaultShellJobRunner
from ratatosk.log import get_logger
import ratatosk.shell as shell

logger = get_logger()

class InputVcfFile(ratatosk.lib.files.input.InputVcfFile):
    pass

class snpEffJobRunner(DefaultShellJobRunner):
    def _make_arglist(self, job):
        if not job.jar() or not os.path.exists(os.path.join(job.path(),job.jar())):
            logger.error("Can't find jar: {0}, full path {1}".format(job.jar(),
                                                                     os.path.abspath(job.jar())))
            raise Exception("job jar does not exist")
        arglist = [job.java()] + job.java_opt() + ['-jar', os.path.join(job.path(), job.jar())]
        if job.main():
            arglist.append(self._get_main(job))
        if job.opts():
            arglist += job.opts()
        (tmp_files, job_args) = DefaultShellJobRunner._fix_paths(job)
        if not job.pipe:
            arglist += job_args
        return (arglist , tmp_files)

    def run_job(self, job):
        (arglist, tmp_files) = self._make_arglist(job)
        cmd = ' '.join(arglist)        
        logger.info("\nJob runner '{0}';\n\trunning command '{1}'".format(self.__class__, cmd))
        (stdout, stderr, returncode) = shell.exec_cmd(cmd, shell=True)
        if returncode == 0:
            logger.info("Shell job completed")
            for a, b in tmp_files:
                logger.info("renaming {0} to {1}".format(a.path, b.path))
                # TODO : this should be relpath?
                a.move(os.path.join(os.curdir, b.path))
                # Some jar programs generate bai or idx files on the fly...
                # FIX ME: is this really needed for snpEff?!?
                # if os.path.exists(a.path + ".bai"):
                #     logger.info("Saw {} file".format(a.path + ".bai"))
                #     os.rename(a.path + ".bai", b.path.replace(".bam", ".bai"))
                # if os.path.exists(a.path + ".idx"):
                #     logger.info("Saw {} file".format(a.path + ".idx"))
                #     os.rename(a.path + ".idx", b.path + ".idx")
        else:
            raise Exception("Job '{}' failed: \n{}".format(cmd, " ".join([stderr])))

class snpEffJobTask(JobTask):
    _snpeff_default_home = os.getenv("SNPEFF_HOME") if os.getenv("SNPEFF_HOME") else os.curdir
    exe_path = luigi.Parameter(default=_snpeff_default_home)
    executable = luigi.Parameter(default="snpEff.jar")
    java_exe = luigi.Parameter(default="java")
    source_suffix = luigi.Parameter(default=".vcf")
    target_suffix = luigi.Parameter(default=".vcf")
    snpeff_config = luigi.Parameter(default=os.path.join(_snpeff_default_home, "snpEff.config"))
    genome = luigi.Parameter(default="GRCh37.64")
    java_options = luigi.Parameter(default=("-Xmx2g",), description="Java options", is_list=True)

    def jar(self):
        return self.executable

    def exe(self):
        return self.jar()

    def java(self):
        return self.java_exe

    def java_opt(self):
        return list(self.java_options)

    def job_runner(self):
        return snpEffJobRunner()


# TODO: add download requirement to snpEff in case database doesn't
# exist
class snpEffDownload(snpEffJobTask):
    pass
    
class snpEff(snpEffJobTask):
    sub_executable = "eff"
    label = luigi.Parameter(default="-effects")
    options = luigi.Parameter(default=("-1",))
    parent_task = luigi.Parameter(default="ratatosk.lib.annotation.snpeff.InputVcfFile")
    suffix = luigi.Parameter(default=(".vcf", ), is_list=True)

    def output(self):
        return luigi.LocalTarget(self.target)
        
    def args(self):
        pcls = self.parent()[0]
        retval = ["-i", pcls().sfx().strip("."),
                  "-o", self.sfx().strip("."),
                  "-c", self.snpeff_config,
                  self.genome,
                  self.input()[0],
                  ">", self.output()
                  ]
        return retval

class snpEffTxt(snpEff):
    suffix = luigi.Parameter(default=(".txt", ), is_list=True)
