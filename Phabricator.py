'''
Copyright 2016 - present The Material Motion Authors. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License"); you may not
use this file except in compliance with the License. You may obtain a copy
of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
License for the specific language governing permissions and limitations
under the License.
'''

import functools
import os
import textwrap

import sublime
import sublime_api
import sublime_plugin

# TODO: abstract this into settings
GIT_PATH = os.environ['HOME'] + "/Projects/material-motion-tools/contributor_tools/git/git"


# Sublime takes the CamelCasedCommand classes, snake_cases their names, and
# exposes them to keybindings and to the `run_command` API.  For example, this
# command is available as `show_stack`.

class ShowStackCommand(sublime_plugin.WindowCommand):
  def run(self):
    git_output = run_mdm_git_command('tree')

    if 'already landed' in git_output:
      self.window.run_command(
        'write_to_panel',
        { 'message': git_output }
      )
      return

    stack = git_output.split('\n')

    commit_regex = re.compile('\* [a-z0-9]{7} (\([^)]+\) )?')
    stack = [re.sub(commit_regex, '', commit) for commit in stack]

    # `show_quick_panel` draws a palette menu with the given `items`.
    self.window.show_quick_panel(
      items = stack,

      # When a menu item is selected, pass its index and `stack` to
      # `on_stack_item_select`
      on_select = functools.partial(
        self.on_stack_item_select,
        stack = stack,
      ),

      # Start the cursor on the bottom of the list
      selected_index = len(stack) - 1,
    )

  def on_stack_item_select(self, menu_index, stack):
    if (menu_index == -1):
      return

    # `menu_index` is 0-indexed from top-to-bottom.  `base_index` is 0-indexed
    # from bottom-to-top.  Convert from one to the other:
    base_index = len(stack) - menu_index - 1

    # If there's a `base_index`, append it to `base`
    base = 'BASE'

    if (base_index != 0):
      base = '+'.join((base, str(base_index)))

    self.window.run_command(
      'write_to_panel',
      { 'message': 'mdm git review %s' % base }
    )


def run_mdm_git_command(command):
  try:
    return run_terminal_command(GIT_PATH, command)
  except FileNotFoundError:
    self.window.run_command(
      'write_to_panel',
      {
        'message': textwrap.dedent('''\
          Error: The Phabricator plugin requires mdm.

          Please install it and try again:

            https://material-motion.github.io/material-motion/team/essentials/frequent_contributors/tools
        ''')
      }
    )


'''
# Helpers #

I tried putting these in a separate file, but Sublime kept complaining:

  TypeError: run_terminal_command() takes 1 positional argument but 2 were
  given

The error doesn't occur if the commands are in the same file.
'''

from subprocess import check_output

import re

def run_terminal_command(*args):
  raw_string = check_output(args).decode('utf-8')

  # Remove formatting characters and extra newline
  return strip_ansi(raw_string)[:-1]


def strip_ansi(text):
    ansi_regex = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]')
    return ansi_regex.sub('', text)


'''
# Panel commands #

Sublime separates the creation of a panel from the insertion of text into it.

This command creates a panel, then writes text to it with WriteTextCommand

Usage:

  self.window.run_command(
    'write_to_panel',
    { 'message': 'purple monkey dishwasher' }
  )
'''

class WriteToPanelCommand(sublime_plugin.WindowCommand):
  def run(self, message):
    panel = self.window.create_output_panel(name = 'phabricator_panel')
    panel.run_command('write_text', {'message': message})
    self.window.run_command('show_panel', {'panel': 'output.phabricator_panel'})


class WriteTextCommand(sublime_plugin.TextCommand):
  def is_visible(self):
    return False

  def run(self, edit, message = ''):
    self.view.set_read_only(False)

    if self.view.size() > 0:
      self.view.erase(
      edit,
      sublime.Region(0, self.view.size())
      )

    self.view.insert(edit, 0, message)
    self.view.set_read_only(True)
