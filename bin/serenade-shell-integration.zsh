# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

#
# Adds escape codes from iTerm to the ZSH shell so we can detect:
# - A: Start of prompt
# - B: End of prompt (start of command)
# - C: End of command (start of output)
# - D: End of output
#
#    [A]prompt% [B] ls -l
#    [C]
#    -rw-r--r-- 1 user group 127 May 1 2016 filename
#    [D]
#

if [[ -o interactive ]]; then
  if [ "${ITERM_SHELL_INTEGRATION_INSTALLED-}" = "" ]; then
    ITERM_SHELL_INTEGRATION_INSTALLED=Yes

    # Mark start of prompt
    iterm2_prompt_mark() {
      printf "\033]133;A\007"
    }

    # Mark end of prompt
    iterm2_prompt_end() {
      printf "\033]133;B\007"
    }

    # Indicates start of command output. Runs just before command executes.
    iterm2_before_cmd_executes() {
      printf "\033]133;C;\007"
    }

    # Report return code of command; runs after command finishes but before prompt
    iterm2_after_cmd_executes() {
      printf "\033]133;D;\007"
    }

    iterm2_decorate_prompt() {
      # This should be a raw PS1 without iTerm2's stuff. It could be changed during command
      # execution.
      ITERM2_PRECMD_PS1="$PS1"

      # Add our escape sequences just before the prompt is shown.
      local PREFIX=""
      if [[ $PS1 == *"$(iterm2_prompt_mark)"* ]]; then
        PREFIX=""
      else
        PREFIX="%{$(iterm2_prompt_mark)%}"
      fi
      PS1="$PREFIX$PS1%{$(iterm2_prompt_end)%}"
    }

    # Runs before a new command
    iterm2_precmd() {
      iterm2_after_cmd_executes
      iterm2_decorate_prompt
    }

    # Runs before a command is executed
    iterm2_preexec() {
      # Set PS1 back to its raw value prior to executing the command.
      PS1="$ITERM2_PRECMD_PS1"
      iterm2_before_cmd_executes
    }

    [[ -z ${precmd_functions-} ]] && precmd_functions=()
    precmd_functions=($precmd_functions iterm2_precmd)

    [[ -z ${preexec_functions-} ]] && preexec_functions=()
    preexec_functions=($preexec_functions iterm2_preexec)
  fi
fi
