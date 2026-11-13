#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""JobsRemoteHost Python 被控端。

这份单文件脚本面向 Windows / macOS 打包：本机显示可见窗口，浏览器端访问后必须等待
被控电脑确认授权，授权前不会返回屏幕画面，也不会执行输入事件。
"""

from __future__ import annotations

# JOBS_TERMINAL_STYLE_GUARD_V1_BEGIN
# 保存与恢复由监督进程负责；导入本模块时不接管终端。
def _jobs_terminal_style_bootstrap_v1():
    import os as _os
    import base64 as _base64
    import json as _json
    import shutil as _shutil
    import subprocess as _subprocess
    import sys as _sys
    import tempfile as _tempfile

    _entry = _os.path.abspath(__file__)
    if _os.environ.get("JOBS_TERMINAL_STYLE_REEXEC") == _entry:
        _os.environ.pop("JOBS_TERMINAL_STYLE_REEXEC", None)
        return
    if (getattr(_sys, "frozen", False) or not _sys.stdin or not _sys.stdout
            or not _sys.stdin.isatty() or not _sys.stdout.isatty()
            or "NO_COLOR" in _os.environ
            or _os.environ.get("PLAIN_OUTPUT") == "1"
            or _os.environ.get("IS_SOURCETREE_RUNTIME") == "1"
            or any(_key.upper().startswith(("SOURCETREE", "SOURCE_TREE"))
                   for _key in _os.environ)):
        return
    if _os.name != "nt" and (_os.environ.get("TERM", "") in ("", "dumb")
                             or _os.environ.get("TMUX") or _os.environ.get("STY")):
        return
    _original = getattr(_sys, "orig_argv", None)
    _module_start = False
    for _argument in list(_original[1:]) if _original else []:
        if _argument == "--" or _os.path.abspath(_argument) == _entry:
            break
        if _argument in ("-c", "-m"):
            _module_start = True
            break
    if _module_start:
        _os.environ.update(NO_COLOR="1", PLAIN_OUTPUT="1", FORCE_COLOR="0", CLICOLOR="0")
        return
    _command = [_sys.executable] + (list(_original[1:]) if _original else list(_sys.argv))
    _environment = _os.environ.copy()
    _environment["JOBS_TERMINAL_STYLE_REEXEC"] = _entry
    _shell_core = r"""# 临时保护当前终端配色，业务进程自行管理原有退出清理。
jobs_terminal_style_run() {
    # 无法可靠保存原色时，沿用脚本已有的纯文本约定。
    jobs_terminal_style_plain() {
        PLAIN_OUTPUT=1
        NO_COLOR=1
        FORCE_COLOR=0
        CLICOLOR=0
        ANSI_COLORS_DISABLED=1
        npm_config_color=false
        export PLAIN_OUTPUT NO_COLOR FORCE_COLOR CLICOLOR ANSI_COLORS_DISABLED npm_config_color
        if "$@"; then
            jobs_style_exit_status=0
        else
            jobs_style_exit_status=$?
        fi
        exit "$jobs_style_exit_status"
    }
    if [ ! -t 0 ] || [ ! -t 1 ] || [ -z "${TERM:-}" ] ||
       [ "${TERM:-}" = dumb ] || [ "${NO_COLOR+x}" = x ] ||
       [ "${PLAIN_OUTPUT:-0}" = 1 ] || [ "${IS_SOURCETREE_RUNTIME:-0}" = 1 ] ||
       env | LC_ALL=C grep -qiE '^(SOURCETREE|SOURCE_TREE)'; then
        if "$@"; then
            jobs_style_exit_status=0
        else
            jobs_style_exit_status=$?
        fi
        exit "$jobs_style_exit_status"
    fi
    if [ -n "${TMUX:-}${STY:-}" ]; then
        jobs_terminal_style_plain "$@"
    fi
    jobs_style_tty=$(tty 2>/dev/null) || jobs_terminal_style_plain "$@"
    if ! ps -o pgid= -o tpgid= -p "$$" 2>/dev/null |
         LC_ALL=C awk 'NF == 2 && $1 == $2 && $1 > 0 { foreground = 1 } END { exit !foreground }'; then
        jobs_terminal_style_plain "$@"
    fi
    case ${JOBS_TERMINAL_STYLE_OWNER:-} in
        ''|*[!0-9]*) ;;
        *)
            if [ "${JOBS_TERMINAL_STYLE_TTY:-}" = "$jobs_style_tty" ] &&
               kill -0 "$JOBS_TERMINAL_STYLE_OWNER" 2>/dev/null; then
                if "$@"; then
                    jobs_style_exit_status=0
                else
                    jobs_style_exit_status=$?
                fi
                exit "$jobs_style_exit_status"
            fi
            ;;
    esac
    jobs_style_stty=$(stty -g 2>/dev/null < /dev/tty) || jobs_terminal_style_plain "$@"
    jobs_style_saved=''
    jobs_style_saved_rows=''
    jobs_style_applied_rows=''
    jobs_style_changed=0
    jobs_style_applied_complete=0
    jobs_style_query_active=0
    jobs_style_recovery=''
    jobs_style_exit_status=0
    jobs_style_esc=$(printf '\033')
    jobs_style_bel=$(printf '\007')
    # 只接受本次请求对应的 RGB 响应；非协议输入使本次探测失败。
    jobs_terminal_style_query() {
        jobs_style_query_key=$1
        printf '\033]%s;?\007' "$jobs_style_query_key" > /dev/tty || return 1
        jobs_style_reply=''
        for jobs_style_attempt in 1 2 3; do
            jobs_style_piece=$(dd bs=256 count=1 2>/dev/null < /dev/tty)
            jobs_style_reply=$jobs_style_reply$jobs_style_piece
            case $jobs_style_reply in
                *"$jobs_style_bel"|*"$jobs_style_esc\\") break ;;
                '') ;;
                "$jobs_style_esc"*) ;;
                *) break ;;
            esac
        done
        case $jobs_style_reply in
            "$jobs_style_esc]$jobs_style_query_key;rgb:"*"$jobs_style_bel")
                jobs_style_rgb=${jobs_style_reply#"$jobs_style_esc]$jobs_style_query_key;rgb:"}
                jobs_style_rgb=${jobs_style_rgb%"$jobs_style_bel"}
                ;;
            "$jobs_style_esc]$jobs_style_query_key;rgb:"*"$jobs_style_esc\\")
                jobs_style_rgb=${jobs_style_reply#"$jobs_style_esc]$jobs_style_query_key;rgb:"}
                jobs_style_rgb=${jobs_style_rgb%"$jobs_style_esc\\"}
                ;;
            *) return 1 ;;
        esac
        jobs_style_normalized=$(printf '%s\n' "$jobs_style_rgb" | LC_ALL=C awk -F/ '
            NF != 3 { exit 1 }
            {
                for (i = 1; i <= 3; i++) {
                    h = tolower($i)
                    if (length(h) < 1 || length(h) > 4 || h ~ /[^0-9a-f]/) exit 1
                    n = 0
                    for (j = 1; j <= length(h); j++) n = n * 16 + index("0123456789abcdef", substr(h, j, 1)) - 1
                    value[i] = int(n * 65535 / (16 ^ length(h) - 1) + 0.5)
                }
                printf "%d/%d/%d", value[1], value[2], value[3]
            }
        ') || return 1
        [ -n "$jobs_style_normalized" ]
    }
    # 查询可用不代表终端允许改色，按目标值核对实际生效结果。
    jobs_terminal_style_accepts_target() {
        jobs_style_requested_hex=''
        case $1 in
            10|12) jobs_style_requested_hex=ffffff ;;
            11) jobs_style_requested_hex=000000 ;;
            '4;'*)
                jobs_style_requested_index=0
                for jobs_style_requested_color in 000000 ff5f56 5fd787 ffd75f 5fafff d787ff 5fd7ff eeeeee 9e9e9e ff8787 87ffaf ffff87 87bfff ffafff afffff ffffff; do
                    if [ "4;$jobs_style_requested_index" = "$1" ]; then
                        jobs_style_requested_hex=$jobs_style_requested_color
                        break
                    fi
                    jobs_style_requested_index=$((jobs_style_requested_index + 1))
                done
                ;;
        esac
        [ -n "$jobs_style_requested_hex" ] || return 1
        printf '%s|%s\n' "$jobs_style_normalized" "$jobs_style_requested_hex" | LC_ALL=C awk -F'|' '
            function hexbyte(h) {
                return (index("0123456789abcdef", substr(h, 1, 1)) - 1) * 16 + index("0123456789abcdef", substr(h, 2, 1)) - 1
            }
            {
                if (split($1, actual, "/") != 3 || length($2) != 6) exit 1
                for (i = 1; i <= 3; i++) {
                    difference = actual[i] - hexbyte(substr($2, i * 2 - 1, 2)) * 257
                    if (difference < -255 || difference > 255) exit 1
                }
            }
        '
    }
    # 检测到后续改色时只恢复仍由本次保护持有的项，保留独立恢复入口。
    jobs_terminal_style_cleanup() {
        jobs_style_result=$1
        trap '' HUP INT TERM
        if [ "$jobs_style_query_active" = 1 ]; then
            stty "$jobs_style_stty" 2>/dev/null < /dev/tty || :
            jobs_style_query_active=0
        fi
        if [ "$jobs_style_changed" = 1 ]; then
            jobs_style_cleanup_ok=0
            jobs_style_conflicts=''
            jobs_style_restore_safe=''
            if [ "$jobs_style_applied_complete" = 1 ]; then
                jobs_style_stty=$(stty -g 2>/dev/null < /dev/tty) || jobs_style_stty=''
                if [ -n "$jobs_style_stty" ] && stty -echo -icanon min 0 time 1 2>/dev/null < /dev/tty; then
                    jobs_style_query_active=1
                    jobs_style_cleanup_ok=1
                    while IFS='|' read -r jobs_style_key jobs_style_expected jobs_style_original; do
                        [ -n "$jobs_style_key" ] || continue
                        if ! jobs_terminal_style_query "$jobs_style_key"; then
                            jobs_style_cleanup_ok=0
                            break
                        fi
                        if [ "$jobs_style_normalized" = "$jobs_style_expected" ]; then
                            jobs_style_restore_safe=$jobs_style_restore_safe$jobs_style_original
                        else
                            jobs_style_conflicts="$jobs_style_conflicts $jobs_style_key"
                        fi
                    done <<JOBS_STYLE_APPLIED
$jobs_style_applied_rows
JOBS_STYLE_APPLIED
                    stty "$jobs_style_stty" 2>/dev/null < /dev/tty || jobs_style_cleanup_ok=0
                    jobs_style_query_active=0
                fi
            fi
            if [ "$jobs_style_cleanup_ok" = 1 ] && printf '%s\033[0m' "$jobs_style_restore_safe" > /dev/tty; then
                if [ -z "$jobs_style_conflicts" ]; then
                    rm -f "$jobs_style_recovery"
                    rmdir "${jobs_style_recovery%/*}" 2>/dev/null || :
                else
                    printf '检测到运行期间的配色变更，已保留这些项：%s\n' "$jobs_style_conflicts" >&2
                    printf '确认要覆盖后续改色时才使用恢复入口：sh "%s"\n' "$jobs_style_recovery" >&2
                    [ "$jobs_style_result" -ne 0 ] || jobs_style_result=1
                fi
            else
                printf '终端配色未能安全自动恢复；确认覆盖当前配色后可运行：sh "%s"\n' "$jobs_style_recovery" >&2
                [ "$jobs_style_result" -ne 0 ] || jobs_style_result=1
            fi
        fi
        if [ "${2:-}" = continue ]; then
            jobs_style_cleanup_status=$jobs_style_result
            return 0
        fi
        exit "$jobs_style_result"
    }
    trap 'jobs_terminal_style_cleanup "$jobs_style_exit_status"' 0
    trap 'jobs_style_exit_status=129; exit 129' HUP
    trap 'jobs_style_exit_status=130; exit 130' INT
    trap 'jobs_style_exit_status=143; exit 143' TERM
    if ! stty -echo -icanon min 0 time 1 2>/dev/null < /dev/tty; then
        jobs_terminal_style_plain "$@"
    fi
    jobs_style_query_active=1
    jobs_style_probe_ok=1
    for jobs_style_key in 10 11 12 '4;0' '4;1' '4;2' '4;3' '4;4' '4;5' '4;6' '4;7' '4;8' '4;9' '4;10' '4;11' '4;12' '4;13' '4;14' '4;15'; do
        if ! jobs_terminal_style_query "$jobs_style_key"; then
            jobs_style_probe_ok=0
            break
        fi
        jobs_style_saved=$jobs_style_saved$jobs_style_reply
        jobs_style_saved_rows="$jobs_style_saved_rows$jobs_style_key|$jobs_style_reply
"
    done
    stty "$jobs_style_stty" 2>/dev/null < /dev/tty || { jobs_style_exit_status=1; exit 1; }
    jobs_style_query_active=0
    if [ "$jobs_style_probe_ok" != 1 ]; then
        printf '%s\n' '终端不支持完整配色保存，或启动时收到其它输入；保留原配色并使用纯文本。' >&2
        jobs_terminal_style_plain "$@"
    fi
    jobs_style_recovery_dir=$(umask 077; mktemp -d "${TMPDIR:-/tmp}/jobs-terminal-style.XXXXXX") || jobs_terminal_style_plain "$@"
    jobs_style_recovery=$jobs_style_recovery_dir/restore.sh
    if ! (umask 077; {
        printf '#!/bin/sh\n'
        printf '[ -t 0 ] && [ "$(tty)" = '\''%s'\'' ] || { printf '\''请在原终端运行恢复入口。\\n'\'' >&2; exit 1; }\n' "$jobs_style_tty"
        printf 'printf '\''本操作会覆盖此终端当前配色。确认恢复脚本启动前的配色，请输入 YES：'\'' >&2\n'
        printf 'IFS= read -r jobs_restore_choice\n[ "$jobs_restore_choice" = YES ] || exit 1\n'
        printf 'printf '\''%%s\\033[0m'\'' '\''%s'\'' > /dev/tty\n' "$jobs_style_saved"
    } > "$jobs_style_recovery"); then
        printf '%s\n' '无法保存终端配色恢复入口；保留原配色并使用纯文本。' >&2
        jobs_terminal_style_plain "$@"
    fi
    printf '正在准备本次终端临时配色；强退后恢复入口：sh "%s"\n' "$jobs_style_recovery" >&2
    jobs_style_changed=1
    printf '\033]10;#ffffff\007\033]11;#000000\007\033]12;#ffffff\007' > /dev/tty
    jobs_style_index=0
    for jobs_style_color in 000000 ff5f56 5fd787 ffd75f 5fafff d787ff 5fd7ff eeeeee 9e9e9e ff8787 87ffaf ffff87 87bfff ffafff afffff ffffff; do
        printf '\033]4;%s;#%s\007' "$jobs_style_index" "$jobs_style_color" > /dev/tty
        jobs_style_index=$((jobs_style_index + 1))
    done
    printf '\033[0m' > /dev/tty
    jobs_style_stty=$(stty -g 2>/dev/null < /dev/tty) || { jobs_style_exit_status=1; exit 1; }
    stty -echo -icanon min 0 time 1 2>/dev/null < /dev/tty || { jobs_style_exit_status=1; exit 1; }
    jobs_style_query_active=1
    jobs_style_probe_ok=1
    jobs_style_targets_ok=1
    while IFS='|' read -r jobs_style_key jobs_style_original; do
        [ -n "$jobs_style_key" ] || continue
        if ! jobs_terminal_style_query "$jobs_style_key"; then
            jobs_style_probe_ok=0
            break
        fi
        jobs_style_applied_rows="$jobs_style_applied_rows$jobs_style_key|$jobs_style_normalized|$jobs_style_original
"
        if ! jobs_terminal_style_accepts_target "$jobs_style_key"; then
            jobs_style_targets_ok=0
        fi
    done <<JOBS_STYLE_ORIGINAL
$jobs_style_saved_rows
JOBS_STYLE_ORIGINAL
    stty "$jobs_style_stty" 2>/dev/null < /dev/tty || { jobs_style_exit_status=1; exit 1; }
    jobs_style_query_active=0
    if [ "$jobs_style_probe_ok" != 1 ]; then
        printf '%s\n' '无法核实本次临时配色，已停止启动业务。' >&2
        jobs_style_exit_status=1
        exit 1
    fi
    jobs_style_applied_complete=1
    if [ "$jobs_style_targets_ok" != 1 ]; then
        jobs_terminal_style_cleanup 0 continue
        jobs_style_changed=0
        if [ "$jobs_style_cleanup_status" != 0 ]; then
            jobs_style_exit_status=1
            exit 1
        fi
        trap 'jobs_style_exit_status=129; exit 129' HUP
        trap 'jobs_style_exit_status=130; exit 130' INT
        trap 'jobs_style_exit_status=143; exit 143' TERM
        printf '%s\n' '终端未接受本次配色，已恢复原配色并使用纯文本。' >&2
        jobs_terminal_style_plain "$@"
    fi
    printf '%s\n' '本次终端已临时使用黑底白字。' >&2
    JOBS_TERMINAL_STYLE_TTY=$jobs_style_tty
    JOBS_TERMINAL_STYLE_OWNER=$$
    export JOBS_TERMINAL_STYLE_TTY JOBS_TERMINAL_STYLE_OWNER
    if "$@"; then
        jobs_style_exit_status=0
    else
        jobs_style_exit_status=$?
    fi
    exit "$jobs_style_exit_status"
}
"""
    _powershell_core = r"""$__jobsTerminalCommand = @($args)
# BEGIN JOBS_TERMINAL_STYLE_V1 - session-only colors; no profile or registry changes.
function New-JobsTerminalStyleState {
    if ($PSVersionTable.PSVersion.Major -lt 5) { return @{ JobsTerminalPlainFallback = $true; Before = @{} } }
    if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT -or $Host.Name -ne 'ConsoleHost') { return $null }
    if ([Console]::IsInputRedirected -or [Console]::IsOutputRedirected -or [Console]::IsErrorRedirected) { return $null }
    if ((Test-Path Env:NO_COLOR) -or $env:TERM -ieq 'dumb' -or $env:PLAIN_OUTPUT -eq '1') { return $null }
    foreach ($key in [Environment]::GetEnvironmentVariables().Keys) {
        if ([string]$key -match '^(?i:SOURCE_?TREE)') { return $null }
    }
    if (-not ('Jobs.TerminalStyleV1.Native' -as [type])) {
        try {
        Add-Type -ErrorAction Stop -TypeDefinition @'
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using System.Text.RegularExpressions;
namespace Jobs.TerminalStyleV1 {
    public static class Native {
        [StructLayout(LayoutKind.Explicit, Size=20, CharSet=CharSet.Unicode)]
        public struct InputRecord {
            [FieldOffset(0)] public ushort Kind;
            [FieldOffset(4)] public int Down;
            [FieldOffset(8)] public ushort Repeat;
            [FieldOffset(10)] public ushort Key;
            [FieldOffset(12)] public ushort Scan;
            [FieldOffset(14)] public char Character;
            [FieldOffset(16)] public uint Modifiers;
        }
        [DllImport("kernel32.dll")] static extern IntPtr GetStdHandle(int n);
        [DllImport("kernel32.dll")] static extern IntPtr GetConsoleWindow();
        [DllImport("kernel32.dll")] static extern bool GetConsoleMode(IntPtr h, out uint mode);
        [DllImport("kernel32.dll")] static extern bool SetConsoleMode(IntPtr h, uint mode);
        [DllImport("kernel32.dll")] static extern uint WaitForSingleObject(IntPtr h, uint milliseconds);
        [DllImport("kernel32.dll")] static extern bool GetNumberOfConsoleInputEvents(IntPtr h, out uint count);
        [DllImport("kernel32.dll", CharSet=CharSet.Unicode, ExactSpelling=true)] static extern bool ReadConsoleInputW(IntPtr h, [Out] InputRecord[] records, uint count, out uint read);
        [DllImport("kernel32.dll", CharSet=CharSet.Unicode, ExactSpelling=true)] static extern bool WriteConsoleInputW(IntPtr h, InputRecord[] records, uint count, out uint written);
        const string OwnerName = "JOBS_TERMINAL_STYLE_WINDOWS_OWNER";
        static readonly string[] Keys = { "10", "11", "4;0", "4;1", "4;2", "4;3", "4;4", "4;5", "4;6", "4;7", "4;8", "4;9", "4;10", "4;11", "4;12", "4;13", "4;14", "4;15" };
        static readonly string[] Hex = { "000000", "ff5f56", "5fd787", "ffd75f", "5fafff", "d787ff", "5fd7ff", "eeeeee", "9e9e9e", "ff8787", "87ffaf", "ffff87", "87bfff", "ffafff", "afffff", "ffffff" };
        static readonly Regex Reply = new Regex("\\x1b\\](?<key>10|11|4;[0-9]{1,2});(?<rgb>rgb:[0-9a-f]{1,4}/[0-9a-f]{1,4}/[0-9a-f]{1,4})(?:\\x07|\\x1b\\\\)", RegexOptions.IgnoreCase);
        public sealed class State {
            public IntPtr Input, Output;
            public uint OutputMode;
            public ConsoleColor Foreground, Background;
            public Dictionary<string,string> Original, Applied;
            public string Owner, PreviousOwner, Recovery;
            public bool Active, ModeChanged, Fallback;
            public Dictionary<string,string> EnvironmentBefore = new Dictionary<string,string>();
        }
        static string Escape(string key, string value) { return "\x1b]" + key + ";" + value + "\x07"; }
        static string Rgb(string hex) { return "rgb:" + hex.Substring(0,2) + "/" + hex.Substring(2,2) + "/" + hex.Substring(4,2); }
        static string Normal(string rgb) {
            string[] parts = rgb.Substring(4).Split('/');
            for (int n=0; n<3; n++) {
                int maximum = (1 << (4 * parts[n].Length)) - 1;
                int value = Convert.ToInt32(parts[n],16);
                parts[n] = ((value * 65535L + maximum/2) / maximum).ToString("x4");
            }
            return String.Join("/",parts);
        }
        // Preserve unrelated key/window records instead of consuming user input during color queries.
        static Dictionary<string,string> Query(State state) {
            uint pending;
            if (!GetNumberOfConsoleInputEvents(state.Input,out pending) || pending != 0) { return null; }
            StringBuilder commands = new StringBuilder();
            foreach (string key in Keys) { commands.Append(Escape(key,"?")); }
            Console.Write(commands.ToString());
            List<InputRecord> records = new List<InputRecord>();
            List<int> characterIndices = new List<int>();
            StringBuilder text = new StringBuilder();
            Dictionary<string,string> result = new Dictionary<string,string>();
            Stopwatch timer = Stopwatch.StartNew();
            try {
                while (timer.ElapsedMilliseconds < 600) {
                    if (result.Count == Keys.Length && GetNumberOfConsoleInputEvents(state.Input,out pending) && pending == 0) { break; }
                    if (WaitForSingleObject(state.Input,20) != 0) { continue; }
                    InputRecord[] item = new InputRecord[1]; uint read;
                    if (!ReadConsoleInputW(state.Input,item,1,out read) || read != 1) { break; }
                    int index = -1;
                    if (item[0].Kind == 1 && item[0].Character != '\0') {
                        if (item[0].Down != 0) { index = text.Length; text.Append(item[0].Character); }
                        else if (text.Length != 0 && text[text.Length-1] == item[0].Character) { index = text.Length-1; }
                    }
                    records.Add(item[0]); characterIndices.Add(index);
                    foreach (Match match in Reply.Matches(text.ToString())) {
                        string key = match.Groups["key"].Value;
                        if (Array.IndexOf(Keys,key) >= 0) { result[key] = match.Groups["rgb"].Value; }
                    }
                }
            } finally {
                bool[] used = new bool[text.Length];
                foreach (Match match in Reply.Matches(text.ToString())) {
                    for (int n=match.Index; n<match.Index+match.Length; n++) { used[n] = true; }
                }
                List<InputRecord> replay = new List<InputRecord>();
                for (int n=0; n<records.Count; n++) {
                    int index = characterIndices[n];
                    if (index < 0 || !used[index]) { replay.Add(records[n]); }
                }
                if (replay.Count != 0) {
                    uint written;
                    if (!WriteConsoleInputW(state.Input,replay.ToArray(),(uint)replay.Count,out written) || written != replay.Count) {
                        Console.Error.WriteLine("[Jobs] Could not replay terminal input; color protection is unavailable.");
                        result.Clear();
                    }
                }
            }
            return result.Count == Keys.Length ? result : null;
        }
        static void Plain(State state) {
            foreach (string key in new string[] { "NO_COLOR", "PLAIN_OUTPUT", "FORCE_COLOR", "CLICOLOR", "ANSI_COLORS_DISABLED" }) {
                state.EnvironmentBefore[key] = Environment.GetEnvironmentVariable(key);
                Environment.SetEnvironmentVariable(key, key == "FORCE_COLOR" || key == "CLICOLOR" ? "0" : "1");
            }
            state.Fallback = true;
        }
        public static void Enter(State state) {
            try {
                state.Input = GetStdHandle(-10); state.Output = GetStdHandle(-11);
                uint inputMode;
                if (!GetConsoleMode(state.Input,out inputMode) || !GetConsoleMode(state.Output,out state.OutputMode)) { Plain(state); return; }
                IntPtr window = GetConsoleWindow();
                if (window == IntPtr.Zero) { Plain(state); return; }
                string identity = window.ToInt64().ToString("x");
                state.PreviousOwner = Environment.GetEnvironmentVariable(OwnerName);
                if (!String.IsNullOrEmpty(state.PreviousOwner)) {
                    string[] owner = state.PreviousOwner.Split(':');
                    int pid; long started;
                    if (owner.Length == 3 && owner[0] == identity && Int32.TryParse(owner[1],out pid) && Int64.TryParse(owner[2],out started)) {
                        try { if (Process.GetProcessById(pid).StartTime.ToUniversalTime().Ticks == started) { return; } } catch {}
                    }
                }
                state.Foreground = Console.ForegroundColor; state.Background = Console.BackgroundColor;
                if ((state.OutputMode & 4) == 0) {
                    if (!SetConsoleMode(state.Output,state.OutputMode | 4)) { Plain(state); return; }
                    state.ModeChanged = true;
                }
                state.Original = Query(state);
                if (state.Original == null) { Restore(state); Plain(state); return; }
                state.Applied = new Dictionary<string,string>();
                state.Applied["10"] = "rgb:ff/ff/ff"; state.Applied["11"] = "rgb:00/00/00";
                for (int n=0; n<16; n++) { state.Applied["4;"+n] = Rgb(Hex[n]); }
                StringBuilder restore = new StringBuilder();
                foreach (string key in Keys) { restore.Append(Escape(key,state.Original[key])); }
                string encoded = Convert.ToBase64String(Encoding.UTF8.GetBytes(restore.ToString()));
                state.Recovery = Path.Combine(Path.GetTempPath(),"JobsTerminalStyle-"+Process.GetCurrentProcess().Id+"-"+Guid.NewGuid().ToString("N")+".ps1");
                string manual = "# Restore only the session colors saved by this Jobs script.\r\n"+
                    "if ([Console]::IsOutputRedirected) { throw 'Run in the original console.' }\r\n"+
                    "Add-Type -Namespace Jobs -Name RecoveryConsole -MemberDefinition '[System.Runtime.InteropServices.DllImport(\"kernel32.dll\")] public static extern System.IntPtr GetStdHandle(int n); [System.Runtime.InteropServices.DllImport(\"kernel32.dll\")] public static extern bool GetConsoleMode(System.IntPtr h, out uint m); [System.Runtime.InteropServices.DllImport(\"kernel32.dll\")] public static extern bool SetConsoleMode(System.IntPtr h, uint m);'\r\n"+
                    "$h = [Jobs.RecoveryConsole]::GetStdHandle(-11); [uint32]$m = 0\r\n"+
                    "if (-not [Jobs.RecoveryConsole]::GetConsoleMode($h, [ref]$m)) { throw 'Run in the original console.' }\r\n"+
                    "try {\r\nif (-not [Jobs.RecoveryConsole]::SetConsoleMode($h, ($m -bor 4))) { throw 'Cannot enable terminal recovery.' }\r\n"+
                    "[Console]::Write([Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('"+encoded+"')))\r\n"+
                    "[Console]::ForegroundColor = [ConsoleColor]"+((int)state.Foreground)+"\r\n"+
                    "[Console]::BackgroundColor = [ConsoleColor]"+((int)state.Background)+"\r\n"+
                    "[Console]::Write([string][char]27 + '[39;49m')\r\n"+
                    "} finally { [void][Jobs.RecoveryConsole]::SetConsoleMode($h, $m) }\r\n";
                File.WriteAllText(state.Recovery,manual,new UTF8Encoding(false));
                state.Owner = identity+":"+Process.GetCurrentProcess().Id+":"+Process.GetCurrentProcess().StartTime.ToUniversalTime().Ticks;
                Environment.SetEnvironmentVariable(OwnerName,state.Owner);
                state.Active = true;
                foreach (string key in Keys) { Console.Write(Escape(key,state.Applied[key])); }
                Console.ForegroundColor = ConsoleColor.White; Console.BackgroundColor = ConsoleColor.Black;
                Dictionary<string,string> check = Query(state);
                foreach (string key in Keys) {
                    if (check == null || Normal(check[key]) != Normal(state.Applied[key])) { Restore(state); Plain(state); return; }
                }
            } catch (Exception error) {
                Restore(state); Plain(state);
                Console.Error.WriteLine("[Jobs] Terminal style unavailable: " + error.Message);
            }
        }
        public static void Restore(State state) {
            if (state == null) { return; }
            try {
                if (state.Active) {
                    Dictionary<string,string> current = Query(state);
                    bool complete = current != null;
                    if (current != null) {
                        bool restoreForeground = Console.ForegroundColor == ConsoleColor.White && Normal(current["10"]) == Normal(state.Applied["10"]) && Normal(current["4;15"]) == Normal(state.Applied["4;15"]);
                        bool restoreBackground = Console.BackgroundColor == ConsoleColor.Black && Normal(current["11"]) == Normal(state.Applied["11"]) && Normal(current["4;0"]) == Normal(state.Applied["4;0"]);
                        foreach (string key in Keys) {
                            if (Normal(current[key]) == Normal(state.Applied[key])) { Console.Write(Escape(key,state.Original[key])); }
                            else if (Normal(current[key]) != Normal(state.Original[key])) {
                                complete = false; Console.Error.WriteLine("[Jobs] Kept a concurrent color change: " + key);
                            }
                        }
                        if (restoreForeground) { Console.ForegroundColor = state.Foreground; Console.Write("\x1b[39m"); }
                        if (restoreBackground) { Console.BackgroundColor = state.Background; Console.Write("\x1b[49m"); }
                    }
                    if (complete) {
                        Dictionary<string,string> check = Query(state);
                        foreach (string key in Keys) { if (check == null || Normal(check[key]) != Normal(state.Original[key])) { complete = false; } }
                    }
                    if (complete) { File.Delete(state.Recovery); }
                    else { Console.Error.WriteLine("[Jobs] Color restore needs review. Manual recovery: powershell -NoProfile -File \""+state.Recovery+"\""); }
                }
            } catch (Exception error) {
                Console.Error.WriteLine("[Jobs] Color restore failed: "+error.Message+"; recovery: "+state.Recovery);
            } finally {
                if (state.Owner != null && Environment.GetEnvironmentVariable(OwnerName) == state.Owner) { Environment.SetEnvironmentVariable(OwnerName,state.PreviousOwner); }
                state.Active = false;
                uint currentMode;
                if (state.ModeChanged && GetConsoleMode(state.Output,out currentMode) && currentMode == (state.OutputMode | 4)) { SetConsoleMode(state.Output,state.OutputMode); }
                state.ModeChanged = false;
                if (state.Fallback) {
                    foreach (KeyValuePair<string,string> pair in state.EnvironmentBefore) {
                        string applied = pair.Key == "FORCE_COLOR" || pair.Key == "CLICOLOR" ? "0" : "1";
                        if (Environment.GetEnvironmentVariable(pair.Key) == applied) { Environment.SetEnvironmentVariable(pair.Key,pair.Value); }
                    }
                    state.Fallback = false;
                }
            }
        }
    }
}
'@
        } catch {
            [Console]::Error.WriteLine('[Jobs] Terminal style setup failed; using plain output: ' + $_.Exception.Message)
            return @{ JobsTerminalPlainFallback = $true; Before = @{} }
        }
    }
    return New-Object Jobs.TerminalStyleV1.Native+State
}
# Guard setup is optional; failure keeps business behavior and the user's original terminal settings.
function Start-JobsTerminalStyle {
    param($State)
    if ($State -is [Collections.IDictionary] -and $State.Contains('JobsTerminalPlainFallback')) {
        foreach ($key in @('NO_COLOR', 'PLAIN_OUTPUT', 'FORCE_COLOR', 'CLICOLOR', 'ANSI_COLORS_DISABLED')) {
            $State.Before[$key] = [Environment]::GetEnvironmentVariable($key)
            [Environment]::SetEnvironmentVariable($key, $(if (@('FORCE_COLOR', 'CLICOLOR') -contains $key) { '0' } else { '1' }))
        }
        return
    }
    if ($null -ne $State) { [Jobs.TerminalStyleV1.Native]::Enter($State) }
}
# A finally block also runs for script exit and Ctrl+C; direct .NET calls avoid stopped pipelines.
function Stop-JobsTerminalStyle {
    param($State)
    if ($State -is [Collections.IDictionary] -and $State.Contains('JobsTerminalPlainFallback')) {
        foreach ($key in $State.Before.Keys) {
            $applied = if (@('FORCE_COLOR', 'CLICOLOR') -contains $key) { '0' } else { '1' }
            if ([Environment]::GetEnvironmentVariable($key) -ceq $applied) { [Environment]::SetEnvironmentVariable($key, $State.Before[$key]) }
        }
        return
    }
    if ($null -ne $State) { [Jobs.TerminalStyleV1.Native]::Restore($State) }
}
# END JOBS_TERMINAL_STYLE_V1

$__jobsTerminalStyleState = $null
$__jobsTerminalExitCode = 0
try {
    $__jobsTerminalStyleState = New-JobsTerminalStyleState
    Start-JobsTerminalStyle $__jobsTerminalStyleState
    if ($null -eq $__jobsTerminalCommand -or $__jobsTerminalCommand.Count -eq 0) { throw 'A program is required.' }
    $__jobsTerminalProgram = $__jobsTerminalCommand[0]
    $__jobsTerminalArguments = @()
    if ($__jobsTerminalCommand.Count -gt 1) { $__jobsTerminalArguments = @($__jobsTerminalCommand[1..($__jobsTerminalCommand.Count-1)]) }
    $LASTEXITCODE = 0
    & $__jobsTerminalProgram @__jobsTerminalArguments
    $__jobsTerminalCommandSucceeded = $?
    $__jobsTerminalExitCode = $LASTEXITCODE
    if (-not $__jobsTerminalCommandSucceeded -and $__jobsTerminalExitCode -eq 0) { $__jobsTerminalExitCode = 1 }
} finally {
    Stop-JobsTerminalStyle $__jobsTerminalStyleState
}
exit $__jobsTerminalExitCode
"""
    _interrupted = False
    # 等监督进程完成恢复后再退出，避免 Ctrl+C 提前关闭控制终端。
    def _wait(_arguments):
        nonlocal _interrupted
        _process = _subprocess.Popen(_arguments, env=_environment)
        while True:
            try:
                return _process.wait()
            except KeyboardInterrupt:
                _interrupted = True
                continue
    try:
        if _os.name == "nt":
            _powershell = _shutil.which("powershell.exe") or _shutil.which("pwsh.exe")
            if not _powershell:
                _os.environ.update(NO_COLOR="1", PLAIN_OUTPUT="1", FORCE_COLOR="0", CLICOLOR="0")
                return
            with _tempfile.TemporaryDirectory(prefix="jobs-terminal-style-") as _directory:
                _wrapper = _os.path.join(_directory, "guard.ps1")
                with open(_wrapper, "w", encoding="utf-8-sig", newline="\n") as _file:
                    _file.write(_powershell_core)
                # 原参数经 JSON 交给原生 Python 数组，避开旧 Windows PowerShell 的参数重解析。
                _environment["JOBS_TERMINAL_STYLE_PYTHON_COMMAND"] = _json.dumps(_command, ensure_ascii=False)
                _receipt = _os.path.join(_directory, "started")
                _environment["JOBS_TERMINAL_STYLE_PYTHON_RECEIPT"] = _receipt
                _bridge_source = """import json, os, subprocess, sys
command = json.loads(os.environ.pop('JOBS_TERMINAL_STYLE_PYTHON_COMMAND'))
with open(os.environ.pop('JOBS_TERMINAL_STYLE_PYTHON_RECEIPT'), 'wb') as receipt:
    receipt.write(b'started')
process = subprocess.Popen(command)
while True:
    try:
        result = process.wait()
        break
    except KeyboardInterrupt:
        continue
sys.exit(result if result >= 0 else 128 - result)
"""
                _bridge = "exec(__import__('base64').b64decode('" + _base64.b64encode(_bridge_source.encode()).decode() + "'))"
                _result = _wait([_powershell, "-NoProfile", "-ExecutionPolicy", "Bypass",
                                 "-File", _wrapper, _sys.executable, "-c", _bridge])
                if not _os.path.exists(_receipt) and not _interrupted and _result not in (129, 130, 143, -1073741510, 0xC000013A):
                    _os.environ.update(NO_COLOR="1", PLAIN_OUTPUT="1", FORCE_COLOR="0", CLICOLOR="0")
                    print("终端配色保护未能启动，保持原配色并使用纯文本。", file=_sys.stderr)
                    return
        else:
            _result = _wait(["/bin/sh", "-c", _shell_core + '\njobs_terminal_style_run "$@"\n',
                             "jobs-terminal-style", *_command])
    except KeyboardInterrupt:
        raise SystemExit(130) from None
    except OSError:
        _os.environ.update(NO_COLOR="1", PLAIN_OUTPUT="1", FORCE_COLOR="0", CLICOLOR="0")
        print("终端配色保护未能启动，保持原配色并使用纯文本。", file=_sys.stderr)
        return
    if _result in (-1073741510, 0xC000013A):
        raise SystemExit(130)
    raise SystemExit(_result if _result >= 0 else 128 - _result)


if __name__ == "__main__":
    _jobs_terminal_style_bootstrap_v1()
# JOBS_TERMINAL_STYLE_GUARD_V1_END

import argparse
import base64
import contextlib
import dataclasses
import http.client
import http.server
import io
import json
import os
import platform
import queue
import random
import re
import secrets
import shutil
import signal
import socket
import socketserver
import string
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

APP_NAME = "JobsRemoteHost"
DEFAULT_PORT = 8088
MAX_FRAME_WIDTH = 1600
JPEG_QUALITY = 58
INVITE_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
VIEWER_HTML_VERSION = "2026-07-01"
MIN_PYTHON = (3, 11)


# 单像素 JPEG，用于自检，避免自检依赖 mss / Pillow。
SELF_TEST_JPEG = base64.b64decode(
    "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////"
    "2wBDAf//////////////////////////////////////////////////////////////////////////////////////wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAX/"
    "xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIQAxAAAAH/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oACAEBAAEFAqf/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oACAEDAQE/ASP/"
    "xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oACAECAQE/ASP/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oACAEBAAY/Aqf/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oACAEBAAE/IV//"
    "2gAMAwEAAgADAAAAEP/EABQRAQAAAAAAAAAAAAAAAAAAABD/2gAIAQMBAT8QH//EABQRAQAAAAAAAAAAAAAAAAAAABD/2gAIAQIBAT8QH//EABQQAQAAAAAAAAAAAAAAAAAAABD/"
    "2gAIAQEAAT8QH//Z"
)


def resource_path(name: str) -> Path:
    """返回源码运行或 PyInstaller 打包后的资源路径。"""

    bundle_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return bundle_root / name


@dataclasses.dataclass(slots=True)
class FrameInfo:
    """记录当前屏幕帧的尺寸信息。"""

    width: int = 0
    height: int = 0
    screen_width: int = 0
    screen_height: int = 0
    left: int = 0
    top: int = 0


@dataclasses.dataclass(slots=True)
class AccessRequest:
    """浏览器访问请求，等待本机窗口弹窗处理。"""

    session_id: str
    invite: str
    mode: str
    remote_addr: str
    created_at: float


@dataclasses.dataclass(slots=True)
class SessionState:
    """浏览器会话状态。"""

    session_id: str
    requested_mode: str
    remote_addr: str
    created_at: float
    status: str = "pending"
    granted_mode: str = "none"
    updated_at: float = dataclasses.field(default_factory=time.time)

    @property
    def can_view(self) -> bool:
        return self.status == "authorized" and self.granted_mode in {"view", "control"}

    @property
    def can_control(self) -> bool:
        return self.status == "authorized" and self.granted_mode == "control"


@dataclasses.dataclass(slots=True)
class AppConfig:
    """运行时配置。"""

    port: int = DEFAULT_PORT
    bind_host: str = "0.0.0.0"
    invite_code: str = ""
    start_tunnel: bool = True
    frame_max_width: int = MAX_FRAME_WIDTH
    jpeg_quality: int = JPEG_QUALITY


class JobsRemoteHostError(RuntimeError):
    """应用级异常。"""


def now_text() -> str:
    """返回适合日志显示的本地时间。"""

    return datetime.now().strftime("%H:%M:%S")


def json_bytes(payload: dict[str, Any]) -> bytes:
    """把对象编码为 HTTP JSON 字节。"""

    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def parse_json_body(handler: http.server.BaseHTTPRequestHandler) -> dict[str, Any]:
    """读取并解析请求体 JSON。"""

    content_length = int(handler.headers.get("Content-Length") or "0")
    raw_body = handler.rfile.read(content_length) if content_length > 0 else b"{}"
    if not raw_body:
        return {}
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise JobsRemoteHostError("请求体不是合法 JSON") from exc
    if not isinstance(payload, dict):
        raise JobsRemoteHostError("请求体必须是 JSON Object")
    return payload


def generate_invite_code(length: int = 6) -> str:
    """生成本轮服务使用的邀请码。"""

    return "".join(secrets.choice(INVITE_ALPHABET) for _ in range(length))


def app_data_dir() -> Path:
    """返回当前平台的应用数据目录。"""

    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(base) / APP_NAME
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME
    return Path.home() / f".{APP_NAME.lower()}"


def log_file_path() -> Path:
    """返回应用日志文件路径。"""

    if sys.platform == "darwin":
        log_dir = Path.home() / "Library" / "Logs" / APP_NAME
    elif os.name == "nt":
        log_dir = app_data_dir() / "logs"
    else:
        log_dir = app_data_dir() / "logs"
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        log_dir = Path(tempfile.gettempdir()) / APP_NAME / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / f"{APP_NAME}.log"


def bundled_base_dir() -> Path:
    """返回源码或 PyInstaller 临时解包目录。"""

    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return Path(meipass)
    return Path(__file__).resolve().parent


def executable_dir() -> Path:
    """返回可执行文件所在目录。"""

    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


class LogSink:
    """同时写 GUI 队列和本地文件的日志器。"""

    def __init__(self, ui_queue: queue.Queue[tuple[str, Any]] | None = None) -> None:
        self.ui_queue = ui_queue
        self.path = log_file_path()
        self._lock = threading.Lock()

    def write(self, message: str) -> None:
        line = f"[{now_text()}] {message}"
        with self._lock:
            with self.path.open("a", encoding="utf-8") as stream:
                stream.write(line + "\n")
        if self.ui_queue is not None:
            self.ui_queue.put(("log", line))


class SessionRegistry:
    """维护浏览器会话和本机授权队列。"""

    def __init__(self, invite_code: str, ui_queue: queue.Queue[tuple[str, Any]], log: LogSink) -> None:
        self.invite_code = invite_code
        self.ui_queue = ui_queue
        self.log = log
        self._lock = threading.RLock()
        self._sessions: dict[str, SessionState] = {}

    def request_access(self, invite: str, mode: str, remote_addr: str) -> SessionState:
        """创建待授权会话。"""

        if invite != self.invite_code:
            raise PermissionError("邀请码错误")
        if mode not in {"view", "control"}:
            raise JobsRemoteHostError("访问模式只能是 view 或 control")
        session_id = secrets.token_urlsafe(18)
        state = SessionState(
            session_id=session_id,
            requested_mode=mode,
            remote_addr=remote_addr,
            created_at=time.time(),
        )
        request = AccessRequest(
            session_id=session_id,
            invite=invite,
            mode=mode,
            remote_addr=remote_addr,
            created_at=state.created_at,
        )
        with self._lock:
            self._sessions[session_id] = state
        self.ui_queue.put(("access_request", request))
        self.log.write(f"浏览器请求{self._mode_text(mode)}，来源 {remote_addr}")
        return state

    def resolve(self, session_id: str, granted_mode: str) -> None:
        """写入本机窗口授权结果。"""

        with self._lock:
            state = self._sessions.get(session_id)
            if state is None:
                return
            state.updated_at = time.time()
            if granted_mode in {"view", "control"}:
                if state.requested_mode == "view" and granted_mode == "control":
                    granted_mode = "view"
                state.status = "authorized"
                state.granted_mode = granted_mode
                self.log.write(f"已授权 {state.remote_addr}：{self._mode_text(granted_mode)}")
            else:
                state.status = "denied"
                state.granted_mode = "none"
                self.log.write(f"已拒绝 {state.remote_addr} 的访问请求")

    def get(self, session_id: str) -> SessionState | None:
        """查询会话状态。"""

        with self._lock:
            return self._sessions.get(session_id)

    def cleanup(self) -> None:
        """清理过期会话。"""

        now = time.time()
        with self._lock:
            expired = [
                session_id
                for session_id, state in self._sessions.items()
                if now - state.updated_at > 3600 or (state.status in {"denied", "pending"} and now - state.created_at > 600)
            ]
            for session_id in expired:
                self._sessions.pop(session_id, None)

    @staticmethod
    def _mode_text(mode: str) -> str:
        """把访问模式转成中文。"""

        return "允许控制" if mode == "control" else "仅观看"


class ScreenCaptureService:
    """负责采集桌面画面并压缩为 JPEG。"""

    def __init__(self, max_width: int, quality: int) -> None:
        self.max_width = max_width
        self.quality = quality
        self.info = FrameInfo()
        self._lock = threading.Lock()
        self._mss: Any | None = None

    def capture_jpeg(self) -> bytes:
        """采集当前屏幕帧。"""

        with self._lock:
            return self._capture_locked()

    def _capture_locked(self) -> bytes:
        """在锁内执行一次屏幕采集。"""

        try:
            import mss
            from PIL import Image
        except ImportError as exc:
            raise JobsRemoteHostError("缺少屏幕采集依赖，请通过打包脚本安装 mss 和 Pillow") from exc

        if self._mss is None:
            self._mss = mss.mss()
        monitor = self._mss.monitors[0]
        shot = self._mss.grab(monitor)
        image = Image.frombytes("RGB", shot.size, shot.rgb)
        original_width, original_height = image.size
        if original_width > self.max_width:
            next_height = max(1, int(original_height * (self.max_width / original_width)))
            image = image.resize((self.max_width, next_height), Image.Resampling.BILINEAR)
        self.info = FrameInfo(
            width=image.size[0],
            height=image.size[1],
            screen_width=original_width,
            screen_height=original_height,
            left=int(monitor.get("left", 0)),
            top=int(monitor.get("top", 0)),
        )
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=self.quality, optimize=True)
        return buffer.getvalue()

    def map_control_event(self, event: dict[str, Any]) -> dict[str, Any]:
        """把浏览器图像坐标映射回真实屏幕坐标。"""

        event_type = str(event.get("type") or "")
        if event_type not in {"mouseMove", "mouseDown", "mouseUp"}:
            return event
        info = self.info
        if info.width <= 0 or info.height <= 0 or info.screen_width <= 0 or info.screen_height <= 0:
            return event
        mapped = dict(event)
        x = float(mapped.get("x") or 0)
        y = float(mapped.get("y") or 0)
        mapped["x"] = int(info.left + (x / info.width) * info.screen_width)
        mapped["y"] = int(info.top + (y / info.height) * info.screen_height)
        return mapped


class SelfTestCaptureService:
    """自检用的假屏幕采集器。"""

    def __init__(self) -> None:
        self.info = FrameInfo(width=1, height=1, screen_width=1, screen_height=1)

    def capture_jpeg(self) -> bytes:
        return SELF_TEST_JPEG

    def map_control_event(self, event: dict[str, Any]) -> dict[str, Any]:
        return event


class InputController:
    """把浏览器控制事件映射到本机鼠标键盘。"""

    KEY_MAP = {
        "Alt": "alt",
        "AltGraph": "alt_gr",
        "Backspace": "backspace",
        "CapsLock": "caps_lock",
        "Control": "ctrl",
        "Delete": "delete",
        "End": "end",
        "Enter": "enter",
        "Escape": "esc",
        "F1": "f1",
        "F2": "f2",
        "F3": "f3",
        "F4": "f4",
        "F5": "f5",
        "F6": "f6",
        "F7": "f7",
        "F8": "f8",
        "F9": "f9",
        "F10": "f10",
        "F11": "f11",
        "F12": "f12",
        "Home": "home",
        "Meta": "cmd",
        "PageDown": "page_down",
        "PageUp": "page_up",
        "Shift": "shift",
        "Space": "space",
        "Tab": "tab",
        "ArrowUp": "up",
        "ArrowDown": "down",
        "ArrowLeft": "left",
        "ArrowRight": "right",
    }

    def __init__(self) -> None:
        self._mouse: Any | None = None
        self._keyboard: Any | None = None

    def apply(self, event: dict[str, Any]) -> None:
        """执行一个浏览器输入事件。"""

        try:
            from pynput import keyboard, mouse
        except ImportError as exc:
            raise JobsRemoteHostError("缺少控制依赖，请通过打包脚本安装 pynput") from exc

        if self._mouse is None:
            self._mouse = mouse.Controller()
        if self._keyboard is None:
            self._keyboard = keyboard.Controller()

        event_type = str(event.get("type") or "")
        if event_type == "mouseMove":
            self._mouse.position = (int(event.get("x") or 0), int(event.get("y") or 0))
        elif event_type in {"mouseDown", "mouseUp"}:
            button = self._mouse_button(mouse, int(event.get("button") or 0))
            if event_type == "mouseDown":
                self._mouse.press(button)
            else:
                self._mouse.release(button)
        elif event_type == "wheel":
            self._mouse.scroll(int(event.get("dx") or 0), int(event.get("dy") or 0))
        elif event_type in {"keyDown", "keyUp"}:
            key = self._keyboard_key(keyboard, str(event.get("key") or ""))
            if key is None:
                return
            if event_type == "keyDown":
                self._keyboard.press(key)
            else:
                self._keyboard.release(key)

    @staticmethod
    def _mouse_button(mouse_module: Any, button_index: int) -> Any:
        """把 DOM 鼠标按钮映射到 pynput。"""

        if button_index == 1:
            return mouse_module.Button.middle
        if button_index == 2:
            return mouse_module.Button.right
        return mouse_module.Button.left

    @classmethod
    def _keyboard_key(cls, keyboard_module: Any, key_name: str) -> Any | None:
        """把 DOM 键名映射到 pynput。"""

        mapped = cls.KEY_MAP.get(key_name)
        if mapped:
            return getattr(keyboard_module.Key, mapped, None)
        if len(key_name) == 1:
            return key_name
        return None


class SelfTestInputController:
    """自检用的假输入控制器。"""

    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def apply(self, event: dict[str, Any]) -> None:
        self.events.append(event)


class NetworkAddressService:
    """枚举本机可展示给访问方的内网地址。"""

    @staticmethod
    def local_http_urls(port: int, invite_code: str) -> list[str]:
        addresses: set[str] = set()
        with contextlib.suppress(Exception):
            hostname = socket.gethostname()
            for item in socket.getaddrinfo(hostname, None, socket.AF_INET, socket.SOCK_STREAM):
                ip = item[4][0]
                if NetworkAddressService._is_usable_ipv4(ip):
                    addresses.add(ip)
        with contextlib.suppress(Exception):
            probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                probe.connect(("8.8.8.8", 80))
                ip = probe.getsockname()[0]
                if NetworkAddressService._is_usable_ipv4(ip):
                    addresses.add(ip)
            finally:
                probe.close()
        if not addresses:
            addresses.add("127.0.0.1")
        query = urllib.parse.urlencode({"invite": invite_code})
        return [f"http://{ip}:{port}/?{query}" for ip in sorted(addresses)]

    @staticmethod
    def _is_usable_ipv4(ip: str) -> bool:
        """过滤回环、链路本地和空地址。"""

        return not (
            ip.startswith("127.")
            or ip.startswith("169.254.")
            or ip == "0.0.0.0"
            or ip.startswith("224.")
            or ip.startswith("255.")
        )


class QuickTunnelService:
    """管理 cloudflared 临时公网通道。"""

    URL_RE = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com", re.IGNORECASE)

    def __init__(self, log: LogSink, event_queue: queue.Queue[tuple[str, Any]]) -> None:
        self.log = log
        self.event_queue = event_queue
        self.process: subprocess.Popen[str] | None = None
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def start(self, port: int, invite_code: str) -> None:
        """启动临时公网通道。"""

        if self.process is not None:
            return
        executable = self.find_cloudflared()
        if executable is None:
            self.log.write("未找到 cloudflared，公网链接暂不可用；可继续使用内网地址")
            self.event_queue.put(("tunnel_error", "未找到 cloudflared"))
            return
        self._stop_event.clear()
        command = [str(executable), "tunnel", "--url", f"http://127.0.0.1:{port}", "--no-autoupdate"]
        self.process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        self.log.write("正在准备免安装公网链接")
        self._thread = threading.Thread(
            target=self._read_output,
            args=(invite_code,),
            name="cloudflared-output",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        """停止临时公网通道。"""

        self._stop_event.set()
        process = self.process
        self.process = None
        if process is None:
            return
        with contextlib.suppress(Exception):
            process.terminate()
        with contextlib.suppress(Exception):
            process.wait(timeout=5)
        if process.poll() is None:
            with contextlib.suppress(Exception):
                process.kill()
        self.log.write("免安装公网通道已停止")

    def _read_output(self, invite_code: str) -> None:
        """解析 cloudflared 输出里的 trycloudflare URL。"""

        assert self.process is not None
        seen_url = ""
        for line in self.process.stdout or []:
            if self._stop_event.is_set():
                break
            clean = line.strip()
            if clean:
                self.log.write(f"cloudflared：{clean}")
            match = self.URL_RE.search(clean)
            if match:
                base_url = match.group(0).rstrip("/")
                if base_url != seen_url:
                    seen_url = base_url
                    public_url = f"{base_url}/?{urllib.parse.urlencode({'invite': invite_code})}"
                    self.event_queue.put(("tunnel_url", public_url))
                    self.log.write(f"免安装公网链接已生成：{public_url}")
        if not self._stop_event.is_set():
            self.event_queue.put(("tunnel_error", "cloudflared 已退出"))
            self.log.write("cloudflared 已退出")

    @staticmethod
    def find_cloudflared() -> Path | None:
        """从打包资源、项目 tools 或 PATH 查找 cloudflared。"""

        binary_name = "cloudflared.exe" if os.name == "nt" else "cloudflared"
        candidates = [
            bundled_base_dir() / "bin" / binary_name,
            executable_dir() / binary_name,
            executable_dir() / "tools" / binary_name,
            Path(__file__).resolve().parent / "tools" / binary_name,
        ]
        for candidate in candidates:
            if candidate.is_file():
                return candidate
        from_path = shutil.which(binary_name)
        return Path(from_path) if from_path else None


class RemoteHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    """浏览器访问端 HTTP 接口。"""

    server_version = f"{APP_NAME}/{VIEWER_HTML_VERSION}"

    @property
    def app_server(self) -> "RemoteHTTPServer":
        return self.server  # type: ignore[return-value]

    def log_message(self, format_text: str, *args: Any) -> None:
        """关闭 BaseHTTPRequestHandler 默认 stderr 日志。"""

    def do_GET(self) -> None:
        """处理 GET 请求。"""

        try:
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path == "/":
                self._send_html(viewer_html())
            elif parsed.path == "/api/info":
                self._send_json(self.app_server.info_payload())
            elif parsed.path == "/api/status":
                self._handle_status(parsed)
            elif parsed.path == "/api/frame":
                self._handle_frame(parsed)
            else:
                self._send_json({"ok": False, "error": "Not Found"}, status=404)
        except Exception as exc:
            self._handle_exception(exc)

    def do_POST(self) -> None:
        """处理 POST 请求。"""

        try:
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path == "/api/request":
                self._handle_request_access()
            elif parsed.path == "/api/control":
                self._handle_control()
            else:
                self._send_json({"ok": False, "error": "Not Found"}, status=404)
        except Exception as exc:
            self._handle_exception(exc)

    def _handle_request_access(self) -> None:
        """处理浏览器申请观看或控制。"""

        payload = parse_json_body(self)
        invite = str(payload.get("invite") or "")
        mode = str(payload.get("mode") or "view")
        remote_addr = self.client_address[0] if self.client_address else "unknown"
        try:
            state = self.app_server.registry.request_access(invite=invite, mode=mode, remote_addr=remote_addr)
        except PermissionError:
            self._send_json({"ok": False, "error": "邀请码错误"}, status=403)
            return
        self._send_json(
            {
                "ok": True,
                "session": state.session_id,
                "status": state.status,
                "requestedMode": state.requested_mode,
            }
        )

    def _handle_status(self, parsed: urllib.parse.ParseResult) -> None:
        """返回浏览器会话状态。"""

        query = urllib.parse.parse_qs(parsed.query)
        session_id = (query.get("session") or [""])[0]
        state = self.app_server.registry.get(session_id)
        if state is None:
            self._send_json({"ok": False, "error": "会话不存在"}, status=404)
            return
        frame = self.app_server.capture.info
        self._send_json(
            {
                "ok": True,
                "status": state.status,
                "requestedMode": state.requested_mode,
                "grantedMode": state.granted_mode,
                "canView": state.can_view,
                "canControl": state.can_control,
                "frameWidth": frame.width,
                "frameHeight": frame.height,
            }
        )

    def _handle_frame(self, parsed: urllib.parse.ParseResult) -> None:
        """返回已授权会话的 JPEG 屏幕帧。"""

        query = urllib.parse.parse_qs(parsed.query)
        session_id = (query.get("session") or [""])[0]
        state = self.app_server.registry.get(session_id)
        if state is None or not state.can_view:
            self._send_json({"ok": False, "error": "未授权"}, status=403)
            return
        try:
            frame = self.app_server.capture.capture_jpeg()
        except Exception as exc:
            self.app_server.log.write(f"采集屏幕失败：{exc}")
            self._send_json({"ok": False, "error": str(exc)}, status=503)
            return
        self.send_response(200)
        self.send_header("Content-Type", "image/jpeg")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(frame)))
        self.end_headers()
        self.wfile.write(frame)

    def _handle_control(self) -> None:
        """执行已授权控制会话的输入事件。"""

        payload = parse_json_body(self)
        session_id = str(payload.get("session") or "")
        state = self.app_server.registry.get(session_id)
        if state is None or not state.can_control:
            self._send_json({"ok": False, "error": "没有控制权限"}, status=403)
            return
        event = payload.get("event")
        if not isinstance(event, dict):
            self._send_json({"ok": False, "error": "缺少控制事件"}, status=400)
            return
        try:
            mapped_event = self.app_server.capture.map_control_event(event)
            self.app_server.input_controller.apply(mapped_event)
        except Exception as exc:
            self.app_server.log.write(f"执行控制事件失败：{exc}")
            self._send_json({"ok": False, "error": str(exc)}, status=503)
            return
        self._send_json({"ok": True})

    def _send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        """发送 JSON 响应。"""

        raw = json_bytes(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _send_html(self, html: str) -> None:
        """发送 HTML 页面。"""

        raw = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _handle_exception(self, exc: Exception) -> None:
        """把异常转换为 HTTP 响应和本机日志。"""

        self.app_server.log.write(f"HTTP 接口异常：{exc}")
        if isinstance(exc, JobsRemoteHostError):
            self._send_json({"ok": False, "error": str(exc)}, status=400)
        else:
            self._send_json({"ok": False, "error": "服务器内部错误"}, status=500)


class RemoteHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    """带应用上下文的多线程 HTTP Server。"""

    daemon_threads = True
    allow_reuse_address = True

    def __init__(
        self,
        server_address: tuple[str, int],
        registry: SessionRegistry,
        capture: ScreenCaptureService | SelfTestCaptureService,
        input_controller: InputController | SelfTestInputController,
        log: LogSink,
    ) -> None:
        super().__init__(server_address, RemoteHTTPRequestHandler)
        self.registry = registry
        self.capture = capture
        self.input_controller = input_controller
        self.log = log

    def info_payload(self) -> dict[str, Any]:
        """返回服务基础信息。"""

        return {
            "ok": True,
            "name": APP_NAME,
            "platform": platform.platform(),
            "version": VIEWER_HTML_VERSION,
        }


class HostServer:
    """控制本地 HTTP 服务生命周期。"""

    def __init__(
        self,
        config: AppConfig,
        registry: SessionRegistry,
        capture: ScreenCaptureService | SelfTestCaptureService,
        input_controller: InputController | SelfTestInputController,
        log: LogSink,
    ) -> None:
        self.config = config
        self.registry = registry
        self.capture = capture
        self.input_controller = input_controller
        self.log = log
        self.httpd: RemoteHTTPServer | None = None
        self.thread: threading.Thread | None = None

    @property
    def is_running(self) -> bool:
        return self.httpd is not None

    @property
    def bound_port(self) -> int:
        if self.httpd is None:
            return self.config.port
        return int(self.httpd.server_address[1])

    def start(self) -> None:
        """启动 HTTP 服务。"""

        if self.httpd is not None:
            return
        self.httpd = RemoteHTTPServer(
            (self.config.bind_host, self.config.port),
            registry=self.registry,
            capture=self.capture,
            input_controller=self.input_controller,
            log=self.log,
        )
        self.thread = threading.Thread(target=self.httpd.serve_forever, name="remote-http-server", daemon=True)
        self.thread.start()
        self.config.port = self.bound_port
        self.log.write(f"服务已开启，端口 {self.bound_port}，邀请码 {self.config.invite_code}")
        self.log.write("HTTP 服务状态：ready")

    def stop(self) -> None:
        """停止 HTTP 服务。"""

        httpd = self.httpd
        self.httpd = None
        if httpd is None:
            return
        httpd.shutdown()
        httpd.server_close()
        self.log.write("服务已停止")


def viewer_html() -> str:
    """返回浏览器观看 / 控制页面。"""

    return r"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>JobsRemoteHost</title>
  <style>
    :root { color-scheme: light dark; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    body { margin: 0; min-height: 100vh; background: #0f172a; color: #e5e7eb; }
    .wrap { max-width: 1120px; margin: 0 auto; padding: 28px 18px 40px; }
    .hero { display: flex; align-items: center; justify-content: space-between; gap: 18px; margin-bottom: 18px; }
    h1 { margin: 0 0 6px; font-size: 30px; letter-spacing: -0.03em; }
    p { margin: 0; color: #94a3b8; }
    .card { background: rgba(15, 23, 42, .86); border: 1px solid rgba(148, 163, 184, .25); border-radius: 18px; padding: 18px; box-shadow: 0 24px 60px rgba(2, 6, 23, .35); }
    .controls { display: grid; grid-template-columns: 1fr auto auto; gap: 10px; align-items: center; }
    input { height: 42px; border-radius: 12px; border: 1px solid rgba(148, 163, 184, .32); background: #111827; color: #e5e7eb; padding: 0 12px; font-size: 17px; outline: none; }
    button { height: 42px; padding: 0 18px; border: 0; border-radius: 12px; background: #2563eb; color: white; font-size: 16px; font-weight: 700; cursor: pointer; }
    button.secondary { background: #334155; }
    button:disabled { opacity: .55; cursor: not-allowed; }
    .status { margin-top: 12px; color: #cbd5e1; min-height: 22px; }
    .screen-wrap { margin-top: 18px; background: #020617; border-radius: 18px; overflow: hidden; border: 1px solid rgba(148, 163, 184, .25); min-height: 420px; display: grid; place-items: center; }
    img { max-width: 100%; display: block; user-select: none; -webkit-user-drag: none; cursor: crosshair; }
    .empty { color: #64748b; padding: 44px; text-align: center; }
    @media (max-width: 720px) { .controls { grid-template-columns: 1fr; } .hero { display: block; } }
  </style>
</head>
<body>
<div class="wrap">
  <div class="hero">
    <div>
      <h1>JobsRemoteHost</h1>
      <p>浏览器访问端。输入邀请码后，本机必须弹窗授权才会显示屏幕。</p>
    </div>
  </div>
  <div class="card">
    <div class="controls">
      <input id="invite" placeholder="输入邀请码" autocomplete="one-time-code">
      <button id="viewBtn">请求观看</button>
      <button id="controlBtn" class="secondary">请求控制</button>
    </div>
    <div id="status" class="status">等待输入邀请码。</div>
  </div>
  <div class="screen-wrap" id="screenWrap">
    <div class="empty" id="empty">授权通过后，这里会显示被控电脑屏幕。</div>
    <img id="screen" alt="Remote screen" hidden>
  </div>
</div>
<script>
const inviteInput = document.getElementById("invite");
const statusEl = document.getElementById("status");
const screen = document.getElementById("screen");
const empty = document.getElementById("empty");
const viewBtn = document.getElementById("viewBtn");
const controlBtn = document.getElementById("controlBtn");
const params = new URLSearchParams(location.search);
inviteInput.value = params.get("invite") || "";
let session = "";
let canControl = false;
let lastMove = 0;
function setStatus(text) { statusEl.textContent = text; }
async function postJson(url, payload) {
  const response = await fetch(url, { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(payload) });
  const data = await response.json().catch(() => ({}));
  if (!response.ok || data.ok === false) throw new Error(data.error || response.statusText);
  return data;
}
async function requestAccess(mode) {
  const invite = inviteInput.value.trim().toUpperCase();
  if (!invite) { setStatus("请先输入邀请码。"); return; }
  viewBtn.disabled = true; controlBtn.disabled = true;
  try {
    const data = await postJson("/api/request", { invite, mode });
    session = data.session;
    setStatus("已发送请求，等待被控电脑确认授权…");
    pollStatus();
  } catch (error) {
    viewBtn.disabled = false; controlBtn.disabled = false;
    setStatus("请求失败：" + error.message);
  }
}
async function pollStatus() {
  if (!session) return;
  try {
    const response = await fetch("/api/status?session=" + encodeURIComponent(session) + "&t=" + Date.now(), { cache: "no-store" });
    const data = await response.json();
    if (!response.ok || !data.ok) throw new Error(data.error || response.statusText);
    if (data.status === "authorized") {
      canControl = !!data.canControl;
      setStatus(canControl ? "已授权控制。移动鼠标或键盘会传到被控电脑。" : "已授权观看。");
      startFrames();
      return;
    }
    if (data.status === "denied") {
      setStatus("被控电脑已拒绝本次访问。");
      viewBtn.disabled = false; controlBtn.disabled = false;
      return;
    }
    setTimeout(pollStatus, 800);
  } catch (error) {
    setStatus("查询状态失败：" + error.message);
    setTimeout(pollStatus, 1200);
  }
}
function startFrames() {
  empty.hidden = true;
  screen.hidden = false;
  const loop = () => {
    if (!session) return;
    screen.src = "/api/frame?session=" + encodeURIComponent(session) + "&t=" + Date.now();
    setTimeout(loop, 180);
  };
  loop();
}
function framePoint(event) {
  const rect = screen.getBoundingClientRect();
  const naturalW = screen.naturalWidth || rect.width;
  const naturalH = screen.naturalHeight || rect.height;
  return {
    x: Math.max(0, Math.round((event.clientX - rect.left) * naturalW / rect.width)),
    y: Math.max(0, Math.round((event.clientY - rect.top) * naturalH / rect.height))
  };
}
function sendControl(event) {
  if (!session || !canControl) return;
  fetch("/api/control", { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({ session, event }) }).catch(() => {});
}
screen.addEventListener("mousemove", event => {
  if (Date.now() - lastMove < 30) return;
  lastMove = Date.now();
  const point = framePoint(event);
  sendControl({ type: "mouseMove", x: point.x, y: point.y });
});
screen.addEventListener("mousedown", event => {
  const point = framePoint(event);
  sendControl({ type: "mouseDown", x: point.x, y: point.y, button: event.button });
});
screen.addEventListener("mouseup", event => {
  const point = framePoint(event);
  sendControl({ type: "mouseUp", x: point.x, y: point.y, button: event.button });
});
screen.addEventListener("wheel", event => {
  event.preventDefault();
  sendControl({ type: "wheel", dx: Math.sign(event.deltaX), dy: -Math.sign(event.deltaY) });
}, { passive: false });
window.addEventListener("keydown", event => sendControl({ type: "keyDown", key: event.key }));
window.addEventListener("keyup", event => sendControl({ type: "keyUp", key: event.key }));
screen.addEventListener("contextmenu", event => event.preventDefault());
viewBtn.addEventListener("click", () => requestAccess("view"));
controlBtn.addEventListener("click", () => requestAccess("control"));
</script>
</body>
</html>"""


class JobsRemoteHostApp:
    """Tkinter 桌面窗口。"""

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.ui_queue: queue.Queue[tuple[str, Any]] = queue.Queue()
        self.log = LogSink(self.ui_queue)
        self.registry = SessionRegistry(config.invite_code, self.ui_queue, self.log)
        self.capture = ScreenCaptureService(config.frame_max_width, config.jpeg_quality)
        self.input_controller = InputController()
        self.host_server = HostServer(config, self.registry, self.capture, self.input_controller, self.log)
        self.tunnel = QuickTunnelService(self.log, self.ui_queue)
        self.root: Any | None = None
        self.port_var: Any | None = None
        self.status_var: Any | None = None
        self.permission_var: Any | None = None
        self.local_urls_text: Any | None = None
        self.public_url_var: Any | None = None
        self.log_text: Any | None = None
        self.start_button: Any | None = None
        self.stop_button: Any | None = None
        self.tray_icon: Any | None = None
        self._quitting = False

    def run(self) -> None:
        """运行 GUI 主循环。"""

        import tkinter as tk
        from tkinter import scrolledtext, ttk

        self.root = tk.Tk()
        self.root.title(APP_NAME)
        self.root.minsize(900, 760)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.bind("<Unmap>", self._on_window_unmap, add="+")
        self._setup_window_icon()
        self._setup_system_tray()

        self.status_var = tk.StringVar(value=f"服务未开启，邀请码：{self.config.invite_code}")
        self.permission_var = tk.StringVar(value=self._permission_status_text())
        self.port_var = tk.StringVar(value=str(self.config.port))
        self.public_url_var = tk.StringVar(value="服务开启后自动准备")

        main = ttk.Frame(self.root, padding=(18, 18, 18, 18))
        main.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        for row in (2, 3, 4):
            main.rowconfigure(row, weight=1)
        main.columnconfigure(0, weight=1)

        title = ttk.Label(main, text=APP_NAME, font=("", 28, "bold"))
        title.grid(row=0, column=0, pady=(0, 8), sticky="ew")
        title.configure(anchor="center")
        ttk.Label(
            main,
            text="推荐用免安装公网链接：朋友只用浏览器访问，本机先弹授权窗口。",
            font=("", 15),
            foreground="#777777",
            anchor="center",
        ).grid(row=1, column=0, pady=(0, 16), sticky="ew")

        control_box = ttk.LabelFrame(main, text="服务控制", padding=(16, 14))
        control_box.grid(row=2, column=0, sticky="ew", pady=(0, 14))
        control_box.columnconfigure(1, weight=1)
        ttk.Label(control_box, text="监听端口", font=("", 13, "bold")).grid(row=0, column=0, padx=(0, 10), sticky="w")
        ttk.Entry(control_box, textvariable=self.port_var, font=("", 14)).grid(row=0, column=1, sticky="ew")
        button_bar = ttk.Frame(control_box)
        button_bar.grid(row=1, column=0, columnspan=2, pady=(14, 0))
        self.start_button = ttk.Button(button_bar, text="开启服务", command=self.start_service)
        self.start_button.grid(row=0, column=0, padx=6)
        self.stop_button = ttk.Button(button_bar, text="停止服务", command=self.stop_service, state="disabled")
        self.stop_button.grid(row=0, column=1, padx=6)
        ttk.Button(button_bar, text="权限说明", command=self.show_permission_help).grid(row=0, column=2, padx=6)
        ttk.Label(control_box, textvariable=self.status_var, anchor="center").grid(row=2, column=0, columnspan=2, pady=(14, 0), sticky="ew")
        ttk.Label(control_box, textvariable=self.permission_var, anchor="center").grid(row=3, column=0, columnspan=2, pady=(6, 0), sticky="ew")

        link_box = ttk.LabelFrame(main, text="连接地址", padding=(16, 14))
        link_box.grid(row=3, column=0, sticky="nsew", pady=(0, 14))
        link_box.columnconfigure(0, weight=1)
        ttk.Label(link_box, text="内网地址", font=("", 13, "bold"), anchor="center").grid(row=0, column=0, sticky="ew")
        self.local_urls_text = scrolledtext.ScrolledText(link_box, height=5, wrap="word", font=("Menlo", 13))
        self.local_urls_text.grid(row=1, column=0, sticky="ew", pady=(8, 14))
        self.local_urls_text.configure(state="disabled")
        ttk.Label(link_box, text="免安装公网链接（推荐）", font=("", 13, "bold"), anchor="center").grid(row=2, column=0, sticky="ew")
        public_entry = ttk.Entry(link_box, textvariable=self.public_url_var, font=("Menlo", 13), justify="center")
        public_entry.grid(row=3, column=0, sticky="ew", pady=(8, 0))

        log_box = ttk.LabelFrame(main, text="日志", padding=(0, 0))
        log_box.grid(row=4, column=0, sticky="nsew")
        log_box.rowconfigure(0, weight=1)
        log_box.columnconfigure(0, weight=1)
        self.log_text = scrolledtext.ScrolledText(log_box, height=10, wrap="word", font=("Menlo", 12))
        self.log_text.grid(row=0, column=0, sticky="nsew")
        self._install_log_context_menu()
        self._refresh_local_urls()
        self._poll_ui_queue()
        self.log.write("窗口已启动")
        self.root.mainloop()

    def _setup_window_icon(self) -> None:
        """为 Tk 窗口设置与菜单栏一致的图标。"""

        if self.root is None:
            return
        try:
            import tkinter as tk

            self._window_icon = tk.PhotoImage(file=str(resource_path("icon.png")))
            self.root.iconphoto(True, self._window_icon)
        except Exception as exc:
            self.log.write(f"窗口图标加载失败，继续使用系统默认图标：{exc}")

    def _setup_system_tray(self) -> None:
        """创建 macOS 顶部菜单栏 / Windows 通知区域图标。"""

        try:
            import pystray
            from PIL import Image

            image = Image.open(resource_path("icon.png")).convert("RGBA")
            menu = pystray.Menu(
                pystray.MenuItem("显示 JobsRemoteHost", self._tray_restore),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("停止服务并退出 JobsRemoteHost", self._tray_quit),
            )
            self.tray_icon = pystray.Icon(APP_NAME, image, APP_NAME, menu)
            self.tray_icon.run_detached()
        except Exception as exc:
            self.tray_icon = None
            self.log.write(f"顶部菜单栏图标不可用，继续使用普通窗口模式：{exc}")

    def _on_window_unmap(self, _event: Any) -> None:
        """黄色最小化按钮触发后，把窗口隐藏到顶部菜单栏。"""

        if self.root is not None:
            self.root.after_idle(self._hide_to_system_tray_if_minimized)

    def _hide_to_system_tray_if_minimized(self) -> None:
        if self.root is None or self.tray_icon is None or self._quitting:
            return
        if self.root.state() == "iconic":
            self.root.withdraw()

    def _tray_restore(self, _icon: Any = None, _item: Any = None) -> None:
        if self.root is not None:
            self.root.after(0, self._restore_from_system_tray)

    def _restore_from_system_tray(self) -> None:
        if self.root is None:
            return
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def _tray_quit(self, _icon: Any = None, _item: Any = None) -> None:
        if self.root is not None:
            self.root.after(0, self._quit_application)

    def _quit_application(self) -> None:
        if self._quitting:
            return
        self._quitting = True
        self.stop_service()
        if self.tray_icon is not None:
            self.tray_icon.stop()
            self.tray_icon = None
        if self.root is not None:
            self.root.destroy()

    def start_service(self) -> None:
        """响应开启服务按钮。"""

        assert self.port_var is not None
        try:
            self.config.port = int(self.port_var.get().strip())
            if not (1 <= self.config.port <= 65535):
                raise ValueError
        except ValueError:
            self.log.write("端口必须是 1-65535 的整数")
            return
        try:
            self.host_server.start()
        except OSError as exc:
            self.log.write(f"开启服务失败：{exc}")
            return
        self._set_running_ui(True)
        self._refresh_local_urls()
        if self.config.start_tunnel:
            self.tunnel.start(self.config.port, self.config.invite_code)

    def stop_service(self) -> None:
        """响应停止服务按钮。"""

        self.tunnel.stop()
        self.host_server.stop()
        self._set_running_ui(False)
        self._set_status(f"服务未开启，邀请码：{self.config.invite_code}")
        if self.public_url_var is not None:
            self.public_url_var.set("服务开启后自动准备")

    def show_permission_help(self) -> None:
        """展示权限说明。"""

        from tkinter import messagebox

        messagebox.showinfo(
            "权限说明",
            "Windows 通常可直接采集与控制。\n\n"
            "macOS 运行打包版时，若系统拦截屏幕录制或辅助功能，请到：\n"
            "系统设置 -> 隐私与安全性 -> 屏幕录制 / 辅助功能，给 JobsRemoteHost 授权。\n\n"
            "无论在哪个平台，浏览器访问都必须经过本机弹窗确认。",
        )

    def _poll_ui_queue(self) -> None:
        """定时消费后台线程事件。"""

        while True:
            try:
                kind, payload = self.ui_queue.get_nowait()
            except queue.Empty:
                break
            if kind == "log":
                self._append_log(str(payload))
            elif kind == "access_request":
                self._show_access_dialog(payload)
            elif kind == "tunnel_url" and self.public_url_var is not None:
                self.public_url_var.set(str(payload))
            elif kind == "tunnel_error" and self.public_url_var is not None:
                self.public_url_var.set(str(payload))
        self.registry.cleanup()
        if self.root is not None:
            self.root.after(250, self._poll_ui_queue)

    def _show_access_dialog(self, request: AccessRequest) -> None:
        """弹出本机授权窗口。"""

        import tkinter as tk
        from tkinter import ttk

        if self.root is None:
            self.registry.resolve(request.session_id, "deny")
            return
        dialog = tk.Toplevel(self.root)
        dialog.title("远程访问请求")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)
        frame = ttk.Frame(dialog, padding=18)
        frame.grid(row=0, column=0, sticky="nsew")
        mode_text = "控制电脑" if request.mode == "control" else "观看屏幕"
        ttk.Label(frame, text="收到浏览器访问请求", font=("", 16, "bold")).grid(row=0, column=0, columnspan=3, sticky="w")
        ttk.Label(frame, text=f"来源：{request.remote_addr}\n请求：{mode_text}\n\n确认后才会开始传输画面。").grid(
            row=1,
            column=0,
            columnspan=3,
            pady=(10, 16),
            sticky="w",
        )

        def resolve(mode: str) -> None:
            self.registry.resolve(request.session_id, mode)
            dialog.destroy()

        if request.mode == "control":
            ttk.Button(frame, text="允许控制", command=lambda: resolve("control")).grid(row=2, column=0, padx=(0, 8))
            ttk.Button(frame, text="仅允许观看", command=lambda: resolve("view")).grid(row=2, column=1, padx=(0, 8))
            ttk.Button(frame, text="拒绝", command=lambda: resolve("deny")).grid(row=2, column=2)
        else:
            ttk.Button(frame, text="允许观看", command=lambda: resolve("view")).grid(row=2, column=0, padx=(0, 8))
            ttk.Button(frame, text="拒绝", command=lambda: resolve("deny")).grid(row=2, column=1, padx=(0, 8))
        dialog.protocol("WM_DELETE_WINDOW", lambda: resolve("deny"))
        self._center_dialog(dialog)

    def _center_dialog(self, dialog: Any) -> None:
        """把授权弹窗居中到主窗口附近。"""

        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        root_x = self.root.winfo_rootx() if self.root is not None else 100
        root_y = self.root.winfo_rooty() if self.root is not None else 100
        root_w = self.root.winfo_width() if self.root is not None else 900
        root_h = self.root.winfo_height() if self.root is not None else 760
        x = root_x + max(0, (root_w - width) // 2)
        y = root_y + max(0, (root_h - height) // 2)
        dialog.geometry(f"+{x}+{y}")

    def _install_log_context_menu(self) -> None:
        """给日志框安装右键菜单。"""

        import tkinter as tk

        if self.log_text is None:
            return
        menu = tk.Menu(self.log_text, tearoff=False)
        menu.add_command(label="复制", command=lambda: self.log_text.event_generate("<<Copy>>"))
        menu.add_command(label="全选", command=self._select_all_logs)
        menu.add_separator()
        menu.add_command(label="清除日志", command=self._clear_logs)

        def popup(event: Any) -> None:
            menu.tk_popup(event.x_root, event.y_root)

        self.log_text.bind("<Button-3>", popup)
        self.log_text.bind("<Control-Button-1>", popup)

    def _select_all_logs(self) -> None:
        """选中日志框全部文字。"""

        if self.log_text is None:
            return
        self.log_text.tag_add("sel", "1.0", "end")
        self.log_text.mark_set("insert", "1.0")
        self.log_text.see("insert")

    def _clear_logs(self) -> None:
        """清空窗口日志。"""

        if self.log_text is None:
            return
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="normal")

    def _append_log(self, line: str) -> None:
        """追加一行窗口日志。"""

        if self.log_text is None:
            return
        self.log_text.configure(state="normal")
        self.log_text.insert("end", line + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="normal")

    def _refresh_local_urls(self) -> None:
        """刷新本机内网地址显示。"""

        if self.local_urls_text is None:
            return
        urls = NetworkAddressService.local_http_urls(self.config.port, self.config.invite_code)
        self.local_urls_text.configure(state="normal")
        self.local_urls_text.delete("1.0", "end")
        self.local_urls_text.insert("end", "\n".join(urls))
        self.local_urls_text.configure(state="disabled")

    def _set_running_ui(self, running: bool) -> None:
        """切换服务按钮状态。"""

        if self.start_button is not None:
            self.start_button.configure(state="disabled" if running else "normal")
        if self.stop_button is not None:
            self.stop_button.configure(state="normal" if running else "disabled")
        self._set_status(f"服务已开启，邀请码：{self.config.invite_code}" if running else f"服务未开启，邀请码：{self.config.invite_code}")

    def _set_status(self, text: str) -> None:
        """更新顶部服务状态。"""

        if self.status_var is not None:
            self.status_var.set(text)

    def _permission_status_text(self) -> str:
        """返回权限提示文案。"""

        if sys.platform == "darwin":
            return "屏幕录制 / 辅助功能：请在系统设置里给打包后的 App 授权"
        if os.name == "nt":
            return "Windows：通常不需要额外系统授权；仍需本机弹窗确认浏览器访问"
        return "Linux：需要桌面环境允许截图与输入注入"

    def _on_close(self) -> None:
        """关闭窗口前停止后台服务。"""

        self._quit_application()


def run_self_test() -> int:
    """执行不依赖 GUI 和第三方库的基础协议自检。"""

    event_queue: queue.Queue[tuple[str, Any]] = queue.Queue()
    config = AppConfig(port=0, bind_host="127.0.0.1", invite_code="TEST42", start_tunnel=False)
    log = LogSink(None)
    registry = SessionRegistry(config.invite_code, event_queue, log)
    capture = SelfTestCaptureService()
    input_controller = SelfTestInputController()
    server = HostServer(config, registry, capture, input_controller, log)
    server.start()
    base = f"http://127.0.0.1:{server.bound_port}"
    try:
        bad_status = _self_test_request_status(base, {"invite": "BAD", "mode": "view"})
        if bad_status != 403:
            raise AssertionError(f"错误邀请码应返回 403，实际 {bad_status}")
        payload = _self_test_post_json(base + "/api/request", {"invite": "TEST42", "mode": "control"})
        session = str(payload["session"])
        kind, request = event_queue.get(timeout=2)
        if kind != "access_request" or request.session_id != session:
            raise AssertionError("授权请求未进入本机队列")
        registry.resolve(session, "control")
        status = _self_test_get_json(base + f"/api/status?session={urllib.parse.quote(session)}")
        if not status.get("canControl"):
            raise AssertionError("授权控制状态错误")
        frame_status, frame_content_type = _self_test_get_status_and_content_type(base + f"/api/frame?session={urllib.parse.quote(session)}")
        if frame_status != 200 or "image/jpeg" not in frame_content_type:
            raise AssertionError("授权后帧接口未返回 JPEG")
        _self_test_post_json(
            base + "/api/control",
            {"session": session, "event": {"type": "mouseMove", "x": 1, "y": 1}},
        )
        if not input_controller.events:
            raise AssertionError("控制事件未写入输入控制器")
    finally:
        server.stop()
    print("SELF_TEST_OK")
    return 0


def _self_test_request_status(base: str, payload: dict[str, Any]) -> int:
    """自检：返回 POST /api/request 的 HTTP 状态码。"""

    request = urllib.request.Request(
        base + "/api/request",
        data=json_bytes(payload),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        urllib.request.urlopen(request, timeout=3).read()
    except urllib.error.HTTPError as exc:
        return exc.code
    return 200


def _self_test_post_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    """自检：POST JSON 并解析响应。"""

    request = urllib.request.Request(
        url,
        data=json_bytes(payload),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=3) as response:
        return json.loads(response.read().decode("utf-8"))


def _self_test_get_json(url: str) -> dict[str, Any]:
    """自检：GET JSON 并解析响应。"""

    with urllib.request.urlopen(url, timeout=3) as response:
        return json.loads(response.read().decode("utf-8"))


def _self_test_get_status_and_content_type(url: str) -> tuple[int, str]:
    """自检：GET 并读取状态码和 Content-Type。"""

    with urllib.request.urlopen(url, timeout=3) as response:
        response.read()
        return int(response.status), str(response.headers.get("Content-Type") or "")


def build_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器。"""

    parser = argparse.ArgumentParser(description="JobsRemoteHost Python 被控端")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="启动 GUI 时默认监听端口")
    parser.add_argument("--no-tunnel", action="store_true", help="启动 GUI 后不自动准备 cloudflared 公网链接")
    parser.add_argument("--self-test", action="store_true", help="执行协议自检后退出")
    return parser


def ensure_python_version() -> None:
    """检查 Python 版本。"""

    if sys.version_info < MIN_PYTHON:
        version_text = ".".join(str(item) for item in MIN_PYTHON)
        raise SystemExit(f"{APP_NAME} 需要 Python {version_text}+")


def main(argv: list[str] | None = None) -> int:
    """命令行入口。"""

    ensure_python_version()
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.self_test:
        return run_self_test()
    config = AppConfig(port=args.port, invite_code=generate_invite_code(), start_tunnel=not args.no_tunnel)
    app = JobsRemoteHostApp(config)
    try:
        app.run()
    except KeyboardInterrupt:
        return 130
    except Exception:
        error_path = log_file_path()
        with error_path.open("a", encoding="utf-8") as stream:
            stream.write(traceback.format_exc() + "\n")
        raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
