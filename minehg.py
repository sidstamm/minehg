#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Original Author: Sid Stamm <sid@mozilla.com>

"""
   Mines hg logs and changes to files for information about things like:
   * who has edited given files
   * top reviewers for a directory
   * reviewer spread

   Usage:
     python minehg.py [<options> ...] <command> [<command args> ...]

   Options:
     --loglimit=N, -l=N      limit mining to the most recent N commits
     --repo=<path>           path to $MOZILLA directory (source tree)

   Commands:
     commitersin             list the committers (and frequency) in a dir
                             (requires one command arg: the directory)

   Examples:
     * to list all the commiters in last 20 changesets in $MOZILLA/content/base :
          python minehg.py -l=20 commitersin content/base
"""


#from __future__ import print_function, unicode_literals

import os
from os.path import basename, dirname, splitext, isfile, isdir, exists, \
                        join, abspath, normpath
import platform
import sys
import getopt
import string
import re
    
def committersin_func(loglimit, repo, args):
  # Open a pipe and start reading data!
  hg_stdin, hg_stdout = os.popen2("hg log -v -l %d -R %s" % (loglimit, repo),
                                   mode='r')

  print "Scanning for commits in:", args

  index = {x: {'users': {}, 'reviewers': {}, 'bugs': {}, 'csets': 0} for x in args}

  state = "init"
  for foo in hg_stdout:

    if state == "desc_end":
      if rec.has_key('files'):
        for path in index:

          # add to index[path] only if one of the files in this cset touched it
          #matches = filter((lambda x: x.startswith(path), rec['files']))
          if any(map(lambda x: x.startswith(path), rec['files'])):
            index[path]['csets'] += 1
            if index[path]['users'].has_key(rec['user']):
              index[path]['users'][rec['user']] += 1
            else :
              index[path]['users'][rec['user']] = 1

            # index bug and reviewers
            if rec.has_key('bug'):
              if index[path]['bugs'].has_key(rec['bug']):
                index[path]['bugs'][rec['bug']] += 1
              else :
                index[path]['bugs'][rec['bug']] = 1

              for r in rec['reviewers']:
                if index[path]['reviewers'].has_key(r):
                  index[path]['reviewers'][r] += 1
                else :
                  index[path]['reviewers'][r] = 1

      # skip to the end
      state = "init"
      continue

    # Reading first line in description
    if state == "desc":
      # in the case of a blank description line, continue
      if foo == "\n":
        state = "desc_end"
        continue
      # extract bug number and reviewers
      bugmatches = re.findall("Bug (\\d+)", foo)
      if len(bugmatches) > 0:
        rec['bug'] = bugmatches[0]
        rec['reviewers'] = re.findall("r=(\\w+)", foo)
      continue

    if state == "init":
      rec = dict()
      state = "reading"
      # rec is {'files': [], 'cset': "", 'user': "", 'bug': "", 'reviewers': []}

    # Reading various lines before description
    if state == "reading":
      try :
        n, v = string.split(foo, sep=":", maxsplit=1)
        if n == "description": 
          state = "desc"
          # start reading the lines of the description
          continue

        if n == "changeset":
          rec['cset'] = string.strip(v)
          continue

        if n == "user":
          rec['user'] = string.strip(v)
          continue

        if n == "files":
          flist = string.split(v)
          rec['files'] = flist
          continue

      except ValueError :
        state = "init"
        continue

  print index

  for p in index:
    print p, ":"
    print "\tcsets: %s" % index[p]['csets']
    print "\tpatch authors %d" % len(index[p]['users'])
    for u in index[p]['users']:
      print "\t  --> (%s) %s" % (index[p]['users'][u], u)
    print "\tbugs: %d" % len(index[p]['bugs'])
    for b in index[p]['bugs']:
      print "\t  --> %s (%s changesets)" % (b, index[p]['bugs'][b])
    print "\treviewers %d" % len(index[p]['reviewers'])
    for r in index[p]['reviewers']:
      print "\t  --> %s (%s changesets)" % (r, index[p]['reviewers'][r])

funcs = {}
funcs['committersin'] = committersin_func

def main(argv):
  global funcs
  loglimit = 10
  repo = "/Users/sstamm/Desktop/mozilla-central"
  optlist, commands = getopt.getopt(argv[1:], 'l', ['loglimit='])

  for opt, optarg in optlist:
    if opt in ('--loglimit', '-l'):
      loglimit = string.atoi(optarg)
    if opt in ('--repo', '-r'):
      repo = optarg

  if len(commands) < 1:
    sys.stdout.write( __doc__ + '\n' )
    return 0

  print('Limiting log parsing to last %s commits\n' % loglimit)

  if funcs.has_key(commands[0]):
    funcs[commands[0]](loglimit=loglimit, repo=repo, args=commands[1:])

  exit(0)

if __name__ == '__main__':
  sys.exit(main(sys.argv))
