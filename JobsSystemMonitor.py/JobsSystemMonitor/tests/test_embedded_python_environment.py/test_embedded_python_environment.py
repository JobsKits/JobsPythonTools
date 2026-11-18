#!/usr/bin/env python3
"""脚本内嵌 Python 预检隔离回归；假 Homebrew / 解释器不联网、不安装真实软件。"""
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

import errno
import json
import os
from pathlib import Path
import select
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest

try:
    import pty
except ImportError:
    pty = None

ENTRY = Path(__file__).resolve().parents[3] / '【MacOS】📦生成dmg.command/【MacOS】📦生成dmg.command'
BLOCK_MARKERS = (
    ('# >>> Jobs Homebrew install choice >>>', '# <<< Jobs Homebrew install choice <<<'),
    ('# >>> Jobs embedded Python runtime >>>', '# <<< Jobs embedded Python runtime <<<'),
)


def embedded_environment_source():
    """从真实交付脚本抽取内嵌函数，不读取任何仓外环境模块。"""
    source = ENTRY.read_text(encoding='utf-8')
    blocks = []
    for start, end in BLOCK_MARKERS:
        first = source.index(start)
        last = source.index(end, first) + len(end)
        blocks.append(source[first:last])
    return '\n'.join(blocks) + '\n'

ZSH = shutil.which('zsh')


@unittest.skipUnless(ZSH and pty and os.name == 'posix', 'Requires zsh and POSIX PTY.')
class PythonRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='jobs-python-runtime-test-')
        self.root = Path(self.temp.name).resolve()
        self.core = self.root / '独立 内嵌环境 🫡.zsh'
        self.core.write_text(embedded_environment_source(), encoding='utf-8')
        self.home = self.root / 'home'
        self.mockbin = self.root / 'bin'
        self.brew_root = self.root / 'brew'
        self.cellar = self.brew_root / 'Cellar'
        self.formula = self.cellar / 'python@3.13' / '3.13.9'
        self.opt = self.brew_root / 'opt' / 'python@3.13'
        self.log = self.root / 'calls.log'
        self.state = self.root / 'runtime.json'
        self.template = self.root / 'python-template'
        for directory in (self.home, self.mockbin, self.formula / 'bin', self.opt.parent):
            directory.mkdir(parents=True, exist_ok=True)
        self.opt.symlink_to(self.formula, target_is_directory=True)
        self.log.touch()
        self.set_state()
        self.write_executable(self.template, '#!' + sys.executable + '\n' + r'''
import builtins, json, os, pathlib, shutil, sys
state = json.loads(pathlib.Path(os.environ['MOCK_STATE']).read_text())
args = sys.argv[1:]
executable = pathlib.Path(sys.argv[0]).resolve()
venv_root = executable.parent.parent
venv_state = venv_root / '.mock-runtime.json'
if venv_state.exists():
    state.update(json.loads(venv_state.read_text()))
if '-m' in args and args[args.index('-m') + 1] == 'venv':
    destination = pathlib.Path(args[-1])
    with open(os.environ['MOCK_LOG'], 'a') as stream:
        stream.write('python:venv:' + str(destination) + '\n')
    if os.environ.get('MOCK_VENV_FAIL') == '1':
        raise SystemExit(31)
    (destination / 'bin').mkdir(parents=True)
    shutil.copyfile(os.environ['MOCK_TEMPLATE'], destination / 'bin/python')
    (destination / 'bin/python').chmod(0o755)
    (destination / 'bin/python3').symlink_to('python')
    (destination / 'pyvenv.cfg').write_text('home = mock\n')
    (destination / '.mock-runtime.json').write_text(json.dumps({'version': state['version'], 'venv': True, 'broken': ''}))
    raise SystemExit(0)
if '-c' not in args:
    raise SystemExit(91)
index = args.index('-c')
code = args[index + 1]
sys.argv = ['-c'] + args[index + 2:]
sys.version_info = tuple(int(piece) for piece in state['version'].split('.')) + ('final', 0)
sys.executable = str(executable)
sys.prefix = str(venv_root if state.get('venv') else pathlib.Path(os.environ['MOCK_FORMULA']))
sys.base_prefix = str(pathlib.Path(os.environ['MOCK_FORMULA']))
original_import = builtins.__import__
def checked_import(name, *args, **kwargs):
    if state.get('broken') and name == state['broken']:
        raise ImportError('mock damaged standard library: ' + name)
    return original_import(name, *args, **kwargs)
builtins.__import__ = checked_import
exec(compile(code, '<runtime-probe>', 'exec'), {'__name__': '__main__'})
''')
        self.install_python()
        self.brew_bin = self.brew_root / 'bin' / 'brew'
        self.brew_bin.parent.mkdir(parents=True)
        self.write_executable(self.brew_bin, '#!' + sys.executable + '\n' + r'''
import json, os, pathlib, shutil, sys
args = sys.argv[1:]
root = pathlib.Path(os.environ['MOCK_BREW_ROOT'])
state_file = pathlib.Path(os.environ['MOCK_STATE'])
state = json.loads(state_file.read_text())
with open(os.environ['MOCK_LOG'], 'a') as stream:
    stream.write('brew:' + ' '.join(args) + '\n')
if args == ['--version']:
    print('Homebrew isolated test')
elif args and args[0] == '--cellar':
    print(root / 'Cellar' / ('python@3.13' if args[1] == 'python' else args[1]) if len(args) > 1 else root / 'Cellar')
elif args and args[0] == '--prefix':
    if len(args) == 1:
        print(root)
    elif state.get('available', True) or os.environ.get('MOCK_MISSING_PREFIX_RETURN') == '1':
        print(root / 'opt' / ('python@3.13' if args[1] == 'python' else args[1]))
    else:
        raise SystemExit(1)
elif args and args[0] in ('list', 'info'):
    if not state.get('available', True):
        raise SystemExit(1)
    print('python@3.13 ' + state['version'])
elif args and args[0] == 'update':
    raise SystemExit(int(os.environ.get('MOCK_UPDATE_FAIL', '0')))
elif args and args[0] in ('install', 'upgrade', 'reinstall'):
    if os.environ.get('MOCK_MUTATION_FAIL') == '1':
        raise SystemExit(23)
    if os.environ.get('MOCK_REPAIR_STILL_BROKEN') != '1':
        state.update(version=os.environ.get('MOCK_TARGET_VERSION', '3.13.9'), broken='', available=True)
        state_file.write_text(json.dumps(state))
        target = pathlib.Path(os.environ['MOCK_FORMULA']) / 'bin/python3.13'
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(os.environ['MOCK_TEMPLATE'], target)
        target.chmod(0o755)
        opt = root / 'opt/python@3.13'
        if opt.is_symlink() and not opt.exists():
            opt.unlink()
        if not opt.exists():
            opt.symlink_to(pathlib.Path(os.environ['MOCK_FORMULA']), target_is_directory=True)
        libexec = pathlib.Path(os.environ['MOCK_FORMULA']) / 'libexec/bin'
        libexec.mkdir(parents=True, exist_ok=True)
        for name in ('python3', 'python'):
            path = libexec / name
            if not path.exists():
                path.symlink_to('../../bin/python3.13')
else:
    raise SystemExit(92)
''')
        self.env = {
            'HOME': str(self.home), 'SHELL': ZSH, 'TERM': 'xterm-256color',
            'PATH': f'{self.mockbin}:/usr/bin:/bin:/usr/sbin:/sbin',
            'TMPDIR': str(self.root) + '/', 'NO_COLOR': '1',
            'MOCK_LOG': str(self.log), 'MOCK_STATE': str(self.state),
            'MOCK_TEMPLATE': str(self.template), 'MOCK_FORMULA': str(self.formula),
            'MOCK_BREW_ROOT': str(self.brew_root), 'MOCK_BREW_BIN': str(self.brew_bin),
        }
        # Only public Homebrew helper boundaries are replaced. Runtime checks execute
        # the real probe body against a harmless Python shim and a real Cellar layout.
        self.prefix = '\nsource ' + shlex.quote(str(self.core)) + '\n' + r'''
jobs_brew_find() {
  print -r -- 'helper:find' >> "$MOCK_LOG"
  [[ "${MOCK_BREW_MISSING:-0}" != 1 ]] || return 1
  print -r -- "$MOCK_BREW_BIN"
}
jobs_brew_choose_installation() {
  print -r -- 'helper:choose' >> "$MOCK_LOG"
  typeset -g JOBS_HOMEBREW_INSTALL_MODE="${MOCK_INSTALL_MODE:-user}"
}
jobs_brew_install_system() {
  print -r -- 'helper:install-system' >> "$MOCK_LOG"
  [[ "${MOCK_BREW_INSTALL_FAIL:-0}" != 1 ]] || return 1
  typeset -g JOBS_HOMEBREW_BIN="$MOCK_BREW_BIN"
}
jobs_brew_install_user() {
  print -r -- 'helper:install-user' >> "$MOCK_LOG"
  [[ "${MOCK_BREW_INSTALL_FAIL:-0}" != 1 ]] || return 1
  typeset -g JOBS_HOMEBREW_BIN="$MOCK_BREW_BIN"
}
jobs_brew_activate() {
  print -r -- "helper:activate:${1:-existing}" >> "$MOCK_LOG"
  [[ "${MOCK_ACTIVATE_FAIL:-0}" != 1 ]] || return 1
  typeset -g JOBS_HOMEBREW_PREFIX="$MOCK_BREW_ROOT"
  export PATH="$MOCK_BREW_ROOT/bin:$PATH"
}

# Real xcode-select is never reached, including on fresh CI machines.
_jobs_python_require_clt_for_install() {
  print -r -- 'helper:clt' >> "$MOCK_LOG"
  [[ "${MOCK_CLT_MISSING:-0}" != 1 ]]
}
'''

    def tearDown(self):
        self.temp.cleanup()

    @staticmethod
    def write_executable(path, content):
        path.write_text(content, encoding='utf-8')
        path.chmod(0o755)

    def set_state(self, version='3.13.9', broken='', available=True):
        self.state.write_text(json.dumps(dict(version=version, broken=broken, available=available)), encoding='utf-8')

    def install_python(self):
        target = self.formula / 'bin' / 'python3.13'
        shutil.copyfile(self.template, target)
        target.chmod(0o755)
        libexec = self.formula / 'libexec/bin'
        libexec.mkdir(parents=True)
        for name in ('python3', 'python'):
            (libexec / name).symlink_to('../../bin/python3.13')

    def runtime(self, version='3.13.9', broken='', available=True):
        self.set_state(version, broken, available)
        if not available:
            for child in (self.formula / 'bin').iterdir():
                child.unlink()

    def venv(self, version='3.13.9', broken='', directory=None):
        directory = directory or self.root / '工具 带空格' / '.venv'
        (directory / 'bin').mkdir(parents=True)
        self.write_executable(directory / 'bin/python', self.template.read_text(encoding='utf-8'))
        (directory / 'bin/python3').symlink_to('python')
        (directory / 'pyvenv.cfg').write_text('home = mock\n', encoding='utf-8')
        (directory / '.mock-runtime.json').write_text(json.dumps(dict(version=version, broken=broken, venv=True)), encoding='utf-8')
        (directory / 'keep-me.txt').write_text('original user dependency and data', encoding='utf-8')
        return directory

    def calls(self):
        return self.log.read_text(encoding='utf-8').splitlines()

    def mutations(self):
        return [line for line in self.calls() if line.startswith(('brew:update', 'brew:install ', 'brew:upgrade ', 'brew:reinstall ', 'python:venv:', 'helper:install-'))]

    def run_pipe(self, code='', env=None, script=None):
        arguments = [ZSH, '-f', str(script)] if script else [ZSH, '-f', '-c', self.prefix + code]
        return subprocess.run(arguments, env=self.env | (env or {}),
                              input='', text=True, capture_output=True, timeout=10)

    def run_tty(self, code='', answer=b'\n', env=None, script=None):
        child_env = self.env | (env or {})
        pid, master = pty.fork()
        if pid == 0:
            arguments = [ZSH, '-f', str(script)] if script else [ZSH, '-f', '-c', self.prefix + code]
            os.execve(ZSH, arguments, child_env)
        output = bytearray()
        deadline = time.monotonic() + 12
        status = None
        try:
            if answer:
                os.write(master, answer)
            while time.monotonic() < deadline:
                if select.select([master], [], [], 0.05)[0]:
                    try:
                        chunk = os.read(master, 65536)
                    except OSError as error:
                        if error.errno != errno.EIO:
                            raise
                        chunk = b''
                    output.extend(chunk)
                waited, wait_status = os.waitpid(pid, os.WNOHANG)
                if waited:
                    status = wait_status
                    break
            if status is None:
                os.kill(pid, signal.SIGKILL)
                os.waitpid(pid, 0)
                raise AssertionError('PTY timed out: ' + output.decode(errors='replace'))
            while select.select([master], [], [], 0)[0]:
                try:
                    chunk = os.read(master, 65536)
                except OSError:
                    break
                if not chunk:
                    break
                output.extend(chunk)
            return os.waitstatus_to_exitcode(status), output.decode(errors='replace')
        finally:
            os.close(master)

    def ensure(self, extra=''):
        return 'jobs_python_ensure 3.11 python@3.13 3.14 || exit $?; ' + extra

    def confirmed(self, extra=''):
        return 'jobs_python_mark_confirmed || exit $?; ' + self.ensure(extra)

    def standalone_entry(self, action):
        """孤立复制交付脚本，仅替换外部工具边界并运行实际内嵌自检。"""
        clone = self.root / '全新电脑 中文 🫡 独立拷贝'
        clone.mkdir()
        entry = clone / ENTRY.name
        source = ENTRY.read_text(encoding='utf-8').rsplit('main "$@"', 1)[0]
        source_line = '\nsource ' + shlex.quote(str(self.core)) + '\n'
        boundaries = self.prefix.split(source_line, 1)[1]
        entry.write_text(source + '\n' + boundaries + '\n' + action + '\n', encoding='utf-8')
        self.assertFalse((clone / 'HomebrewSupport').exists())
        self.assertFalse((clone.parent / 'HomebrewSupport').exists())
        return entry

    def test_isolated_script_checks_runtime_without_external_modules(self):
        entry = self.standalone_entry(
            'prepare_display_paths; jobs_python_mark_confirmed; check_environment; '
            'print -r -- STANDALONE_READY')
        code, output = self.run_tty(script=entry)
        self.assertEqual(code, 0, output)
        self.assertIn('STANDALONE_READY', output)
        self.assertEqual(self.mutations(), ['brew:update'])

    def test_isolated_script_runtime_failure_stops_without_business(self):
        entry = self.standalone_entry(
            'prepare_display_paths; jobs_python_mark_confirmed; check_environment; '
            'print -r -- BUSINESS')
        code, output = self.run_tty(script=entry, env={'MOCK_UPDATE_FAIL': '19'})
        self.assertNotEqual(code, 0, output)
        self.assertNotIn('BUSINESS', output)
        self.assertEqual(self.mutations(), ['brew:update'])

    def test_isolated_script_cancellation_stops_without_any_mutation(self):
        entry = self.standalone_entry('prepare_display_paths; check_environment; print -r -- BUSINESS')
        code, output = self.run_tty(script=entry, answer=b' \n')
        self.assertNotEqual(code, 0, output)
        self.assertEqual(self.mutations(), [])

    def test_source_has_no_probes_or_writes(self):
        result = self.run_pipe('print -r -- SOURCE_READY')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('SOURCE_READY', result.stdout)
        self.assertEqual(self.calls(), [])

    def test_healthy_readonly_runtime_works_without_tty(self):
        result = self.run_pipe(self.ensure('print -r -- "SELECTED:$JOBS_PYTHON_BIN"'))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('SELECTED:', result.stdout)
        self.assertEqual(self.mutations(), [])

    def test_sourcetree_healthy_runtime_is_readonly(self):
        result = self.run_pipe(self.ensure(), {'IS_SOURCETREE_RUNTIME': '1'})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.mutations(), [])

    def test_tty_without_confirmation_only_reads_healthy_runtime(self):
        code, output = self.run_tty(self.ensure())
        self.assertEqual(code, 0, output)
        self.assertEqual(self.mutations(), [])

    def test_selected_runtime_and_path_are_exported_without_clobbering_venv(self):
        result = self.run_pipe('PYTHON_BIN=existing-venv; ' + self.ensure(
            'print -r -- "VENV:$PYTHON_BIN"; print -r -- "PATH_HEAD:${path[1]}"; /usr/bin/env'))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('VENV:existing-venv', result.stdout)
        self.assertIn('JOBS_PYTHON_BIN=', result.stdout)
        self.assertIn('PATH_HEAD:', result.stdout)

    def test_path_python3_resolves_to_selected_brew_runtime(self):
        result = self.run_pipe(self.ensure(
            'print -r -- "PATH_PYTHON:$(command -v python3)"; '
            'python3 -c \'import sys; print("EXECUTED:" + sys.executable)\''))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('PATH_PYTHON:' + str(self.opt / 'libexec/bin/python3'), result.stdout)
        self.assertIn('EXECUTED:' + str(self.formula / 'bin/python3.13'), result.stdout)

    def test_unversioned_python_formula_alias_uses_canonical_cellar(self):
        result = self.run_pipe('jobs_python_ensure 3.11 python 3.14 || exit $?; print -r -- "SELECTED:$JOBS_PYTHON_BIN"')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('SELECTED:', result.stdout)
        self.assertEqual(self.mutations(), [])

    def test_confirmed_healthy_runtime_updates_brew_once_but_not_python(self):
        code, output = self.run_tty(self.confirmed(self.ensure()))
        self.assertEqual(code, 0, output)
        self.assertEqual(self.calls().count('brew:update'), 1)
        self.assertEqual(self.mutations(), ['brew:update'])

    def test_update_failure_stops_before_runtime_mutation(self):
        self.runtime(version='3.9.6')
        code, output = self.run_tty(self.confirmed('print -r -- BUSINESS'), env={'MOCK_UPDATE_FAIL': '17'})
        self.assertNotEqual(code, 0, output)
        self.assertNotIn('BUSINESS', output)
        self.assertEqual(self.mutations(), ['brew:update'])

    def test_failed_brew_update_is_not_cached_as_success(self):
        code, output = self.run_tty(
            'jobs_python_mark_confirmed; if jobs_python_ensure 3.11 python@3.13 3.14; then exit 98; fi; '
            'export MOCK_UPDATE_FAIL=0; ' + self.ensure(), env={'MOCK_UPDATE_FAIL': '17'})
        self.assertEqual(code, 0, output)
        self.assertEqual(self.mutations(), ['brew:update', 'brew:update'])

    def test_confirm_prepare_enter_authorizes_update(self):
        code, output = self.run_tty('jobs_python_confirm_prepare || exit $?; ' + self.ensure())
        self.assertEqual(code, 0, output)
        self.assertEqual(self.mutations(), ['brew:update'])

    def test_confirm_prepare_does_not_prompt_twice_in_confirmed_process(self):
        code, output = self.run_tty(
            'jobs_python_confirm_prepare || exit $?; jobs_python_confirm_prepare || exit $?; ' + self.ensure())
        self.assertEqual(code, 0, output)
        self.assertEqual(output.count('➤ 按回车准备环境'), 1)
        self.assertEqual(self.mutations(), ['brew:update'])

    def test_confirm_prepare_nonempty_or_space_cancels_without_writes(self):
        for answer in (b'cancel\n', b' \n'):
            with self.subTest(answer=answer):
                code, output = self.run_tty('jobs_python_confirm_prepare || exit $?; ' + self.ensure(), answer)
                self.assertNotEqual(code, 0, output)
                self.assertEqual(self.mutations(), [])

    def test_confirm_prepare_eof_stops_without_writes(self):
        code, output = self.run_tty('jobs_python_confirm_prepare || exit $?; ' + self.ensure(), b'\x04')
        self.assertNotEqual(code, 0, output)
        self.assertEqual(self.mutations(), [])

    def test_confirm_prepare_non_tty_cannot_authorize_mutation(self):
        result = self.run_pipe('jobs_python_confirm_prepare || exit $?; ' + self.ensure())
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.mutations(), [])

    def test_environment_cannot_fake_process_confirmation_or_updated_brew(self):
        self.runtime(version='3.9.6')
        result = self.run_pipe(self.ensure(), {
            '_JOBS_PYTHON_CONFIRMED_PROCESS': '1', '_JOBS_PYTHON_UPDATED_BREWS': '1',
            'JOBS_PYTHON_CONFIRMED': '1', 'JOBS_PYTHON_PREPARED': '1',
        })
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.mutations(), [])

    def test_fake_environment_updated_token_does_not_skip_real_update(self):
        code, output = self.run_tty(self.confirmed(), env={'_JOBS_PYTHON_UPDATED_BREWS': str(self.brew_bin)})
        self.assertEqual(code, 0, output)
        self.assertEqual(self.calls().count('brew:update'), 1)

    def test_even_exact_exported_process_token_cannot_authorize_writes(self):
        self.runtime(version='3.9.6')
        code, output = self.run_tty(
            'export _JOBS_PYTHON_CONFIRMED_PROCESS="$$:$((ZSH_SUBSHELL + 1))"; ' + self.ensure())
        self.assertNotEqual(code, 0, output)
        self.assertEqual(self.mutations(), [])

    def test_subshell_cannot_inherit_parent_write_authorization(self):
        self.runtime(version='3.9.6')
        code, output = self.run_tty(
            'jobs_python_mark_confirmed; ( ' + self.ensure() + ' )')
        self.assertNotEqual(code, 0, output)
        self.assertEqual(self.mutations(), [])

    def test_missing_python_non_tty_stops_without_write(self):
        self.runtime(available=False)
        result = self.run_pipe(self.ensure())
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.mutations(), [])

    def test_low_python_non_tty_stops_without_write(self):
        self.runtime(version='3.9.6')
        result = self.run_pipe(self.ensure())
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.mutations(), [])

    def test_missing_brew_non_tty_stops_before_choice_or_install(self):
        result = self.run_pipe(self.ensure(), {'MOCK_BREW_MISSING': '1'})
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('helper:choose', self.calls())
        self.assertEqual(self.mutations(), [])

    def test_sourcetree_missing_runtime_never_installs(self):
        self.runtime(available=False)
        result = self.run_pipe(self.ensure(), {'IS_SOURCETREE_RUNTIME': '1'})
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.mutations(), [])

    def test_missing_runtime_installs_formula_and_rechecks(self):
        self.runtime(available=False)
        code, output = self.run_tty(self.confirmed('print -r -- "READY:$JOBS_PYTHON_BIN"'))
        self.assertEqual(code, 0, output)
        self.assertEqual(self.mutations(), ['brew:update', 'brew:install python@3.13'])
        self.assertIn('READY:', output)

    def test_required_python_install_prompt_rejects_space_or_eof(self):
        self.runtime(available=False)
        for answer in (b' \n', b'\x04'):
            with self.subTest(answer=answer):
                self.log.write_text('', encoding='utf-8')
                code, output = self.run_tty(self.confirmed(), answer)
                self.assertNotEqual(code, 0, output)
                self.assertEqual(self.mutations(), ['brew:update'])

    def test_uninstalled_formula_prefix_may_print_missing_path_successfully(self):
        self.runtime(available=False)
        self.opt.unlink()
        code, output = self.run_tty(self.confirmed(), env={'MOCK_MISSING_PREFIX_RETURN': '1'})
        self.assertEqual(code, 0, output)
        self.assertEqual(self.mutations(), ['brew:update', 'brew:install python@3.13'])

    def test_dangling_formula_opt_inside_its_cellar_is_repaired(self):
        self.opt.unlink()
        self.opt.symlink_to(self.cellar / 'python@3.13/missing-version', target_is_directory=True)
        code, output = self.run_tty(self.confirmed())
        self.assertEqual(code, 0, output)
        self.assertEqual(self.mutations(), ['brew:update', 'brew:reinstall python@3.13'])

    def test_low_runtime_upgrades_formula_and_rechecks(self):
        self.runtime(version='3.9.6')
        code, output = self.run_tty(self.confirmed())
        self.assertEqual(code, 0, output)
        self.assertEqual(self.mutations(), ['brew:update', 'brew:upgrade python@3.13'])

    def test_damaged_stdlib_reinstalls_only_once(self):
        self.runtime(broken='venv')
        code, output = self.run_tty(self.confirmed())
        self.assertEqual(code, 0, output)
        self.assertEqual(self.mutations(), ['brew:update', 'brew:reinstall python@3.13'])

    def test_tomllib_is_checked_for_python_311_or_later(self):
        self.runtime(broken='tomllib')
        code, output = self.run_tty(self.confirmed())
        self.assertEqual(code, 0, output)
        self.assertIn('brew:reinstall python@3.13', self.mutations())

    def test_repair_failure_stops_business(self):
        self.runtime(version='3.9.6')
        code, output = self.run_tty(self.confirmed('print -r -- BUSINESS'), env={'MOCK_MUTATION_FAIL': '1'})
        self.assertNotEqual(code, 0, output)
        self.assertNotIn('BUSINESS', output)
        self.assertEqual(self.mutations(), ['brew:update', 'brew:upgrade python@3.13'])

    def test_failed_post_repair_check_stops_without_retry_loop(self):
        self.runtime(broken='venv')
        code, output = self.run_tty(self.confirmed('print -r -- BUSINESS'), env={'MOCK_REPAIR_STILL_BROKEN': '1'})
        self.assertNotEqual(code, 0, output)
        self.assertNotIn('BUSINESS', output)
        self.assertEqual(self.mutations(), ['brew:update', 'brew:reinstall python@3.13'])

    def test_maximum_exclusive_rejects_newer_incompatible_runtime(self):
        self.runtime(version='3.14.0')
        result = self.run_pipe(self.ensure())
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.mutations(), [])

    def test_confirmed_newer_incompatible_runtime_is_not_upgraded(self):
        self.runtime(version='3.14.0')
        code, output = self.run_tty(self.confirmed())
        self.assertNotEqual(code, 0, output)
        self.assertEqual(self.mutations(), ['brew:update'])

    def test_formula_escape_or_invalid_version_stops_without_writes(self):
        for arguments in ('broken python@3.13', '3.11 ../python', '3.11 python@3.13 3.10'):
            with self.subTest(arguments=arguments):
                result = self.run_pipe('jobs_python_ensure ' + arguments)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(self.mutations(), [])

    def test_formula_opt_link_outside_cellar_is_rejected(self):
        foreign = self.root / 'foreign-python'
        (foreign / 'bin').mkdir(parents=True)
        self.write_executable(foreign / 'bin/python3.13', self.template.read_text(encoding='utf-8'))
        self.opt.unlink()
        self.opt.symlink_to(foreign, target_is_directory=True)
        result = self.run_pipe(self.ensure())
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.mutations(), [])

    def test_python_executable_link_outside_formula_is_rejected(self):
        foreign = self.root / 'foreign-python'
        self.write_executable(foreign, self.template.read_text(encoding='utf-8'))
        (self.formula / 'bin/python3.13').unlink()
        (self.formula / 'bin/python3.13').symlink_to(foreign)
        result = self.run_pipe(self.ensure())
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.mutations(), [])

    def test_missing_brew_install_uses_existing_choice_module_and_updates(self):
        code, output = self.run_tty(self.confirmed(), env={'MOCK_BREW_MISSING': '1'})
        self.assertEqual(code, 0, output)
        self.assertIn('helper:choose', self.calls())
        self.assertEqual(self.mutations(), ['helper:install-user', 'brew:update'])

    def test_failed_brew_install_stops_without_update_or_python_install(self):
        code, output = self.run_tty(self.confirmed(), env={'MOCK_BREW_MISSING': '1', 'MOCK_BREW_INSTALL_FAIL': '1'})
        self.assertNotEqual(code, 0, output)
        self.assertEqual(self.mutations(), ['helper:install-user'])

    def test_unavailable_clt_stops_before_brew_installation(self):
        code, output = self.run_tty(self.confirmed(), env={'MOCK_BREW_MISSING': '1', 'MOCK_CLT_MISSING': '1'})
        self.assertNotEqual(code, 0, output)
        self.assertIn('helper:clt', self.calls())
        self.assertNotIn('helper:choose', self.calls())
        self.assertEqual(self.mutations(), [])

    def test_new_venv_uses_selected_runtime_and_supports_spaces(self):
        destination = self.root / '项目 中文' / '.venv'
        quoted = shlex.quote(str(destination))
        code, output = self.run_tty(self.confirmed(f'jobs_python_prepare_venv {quoted} 3.11 3.14 || exit $?; print -r -- VENV_READY'))
        self.assertEqual(code, 0, output)
        self.assertTrue((destination / 'bin/python').exists())
        self.assertIn('VENV_READY', output)
        self.assertEqual(len([item for item in self.calls() if item.startswith('python:venv:')]), 1)

    def test_healthy_venv_is_reused_without_mutation(self):
        destination = self.venv()
        before = (destination / 'keep-me.txt').read_bytes()
        result = self.run_pipe(self.ensure(f'jobs_python_prepare_venv {shlex.quote(str(destination))} 3.11 3.14'))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((destination / 'keep-me.txt').read_bytes(), before)
        self.assertEqual(self.mutations(), [])
        self.assertEqual(len(list(destination.parent.glob('.venv*'))), 1)

    def test_old_venv_is_fully_preserved_in_backup_before_recreation(self):
        destination = self.venv(version='3.9.6')
        code, output = self.run_tty(self.confirmed(f'jobs_python_prepare_venv {shlex.quote(str(destination))} 3.11 3.14 || exit $?'), b'\n')
        self.assertEqual(code, 0, output)
        backups = [path for path in destination.parent.iterdir() if path != destination and path.is_dir()]
        self.assertEqual(len(backups), 1, output)
        self.assertEqual((backups[0] / 'keep-me.txt').read_text(encoding='utf-8'), 'original user dependency and data')
        self.assertFalse((destination / 'keep-me.txt').exists())

    def test_damaged_venv_recreation_requires_its_own_enter(self):
        destination = self.venv(broken='venv')
        code, output = self.run_tty(self.confirmed(f'jobs_python_prepare_venv {shlex.quote(str(destination))} 3.11 3.14 || exit $?'), b'cancel\n')
        self.assertNotEqual(code, 0, output)
        self.assertTrue((destination / 'keep-me.txt').exists())
        self.assertEqual(len(list(destination.parent.iterdir())), 1)
        self.assertFalse(any(line.startswith('python:venv:') for line in self.calls()))

    def test_old_venv_space_and_eof_cancel_without_rename(self):
        destination = self.venv(version='3.9.6')
        for answer in (b' \n', b'\x04'):
            with self.subTest(answer=answer):
                code, output = self.run_tty(self.confirmed(f'jobs_python_prepare_venv {shlex.quote(str(destination))} 3.11 3.14 || exit $?'), answer)
                self.assertNotEqual(code, 0, output)
                self.assertTrue((destination / 'keep-me.txt').exists())
                self.assertEqual(len(list(destination.parent.iterdir())), 1)
                self.assertFalse(any(line.startswith('python:venv:') for line in self.calls()))

    def test_bad_venv_non_tty_is_never_renamed(self):
        destination = self.venv(version='3.9.6')
        result = self.run_pipe(self.ensure(f'jobs_python_prepare_venv {shlex.quote(str(destination))} 3.11 3.14'))
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue((destination / 'keep-me.txt').exists())
        self.assertEqual(self.mutations(), [])

    def test_new_venv_non_tty_is_not_created(self):
        destination = self.root / 'project' / '.venv'
        result = self.run_pipe(self.ensure(f'jobs_python_prepare_venv {shlex.quote(str(destination))} 3.11 3.14'))
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(destination.exists())
        self.assertEqual(self.mutations(), [])

    def test_inherited_runtime_variable_cannot_create_venv(self):
        destination = self.root / 'project' / '.venv'
        code, output = self.run_tty(
            'jobs_python_mark_confirmed; '
            f'jobs_python_prepare_venv {shlex.quote(str(destination))} 3.11 3.14 || exit $?',
            env={'JOBS_PYTHON_BIN': str(self.formula / 'bin/python3.13')})
        self.assertNotEqual(code, 0, output)
        self.assertFalse(destination.exists())
        self.assertEqual(self.mutations(), [])

    def test_selected_runtime_is_rechecked_against_venv_version_bounds(self):
        destination = self.root / 'project' / '.venv'
        code, output = self.run_tty(self.confirmed(
            f'jobs_python_prepare_venv {shlex.quote(str(destination))} 3.14 3.15 || exit $?'))
        self.assertNotEqual(code, 0, output)
        self.assertFalse(destination.exists())
        self.assertEqual(self.mutations(), ['brew:update'])

    def test_venv_rejects_symlink_root_home_and_source_directory(self):
        actual = self.venv()
        link = self.root / 'venv-link'
        link.symlink_to(actual, target_is_directory=True)
        for destination in (link, Path('/'), self.home, self.root):
            with self.subTest(destination=destination):
                result = self.run_pipe(self.ensure(f'jobs_python_prepare_venv {shlex.quote(str(destination))} 3.11 3.14'))
                self.assertNotEqual(result.returncode, 0)
                self.assertTrue((actual / 'keep-me.txt').exists())
                self.assertEqual(self.mutations(), [])

    def test_ordinary_source_directory_is_not_renamed_after_confirmation(self):
        source = self.root / 'project-source'
        source.mkdir()
        (source / 'app.py').write_text('print("user source")\n', encoding='utf-8')
        code, output = self.run_tty(self.confirmed(
            f'jobs_python_prepare_venv {shlex.quote(str(source))} 3.11 3.14 || exit $?'))
        self.assertNotEqual(code, 0, output)
        self.assertTrue((source / 'app.py').exists())
        self.assertFalse(any(self.root.glob('project-source.backup.*')))
        self.assertFalse(any(line.startswith('python:venv:') for line in self.calls()))

    def test_symbolic_link_in_venv_parent_is_rejected(self):
        actual = self.root / 'real-project'
        actual.mkdir()
        link = self.root / 'linked-project'
        link.symlink_to(actual, target_is_directory=True)
        code, output = self.run_tty(self.confirmed(
            f'jobs_python_prepare_venv {shlex.quote(str(link / ".venv"))} 3.11 3.14 || exit $?'))
        self.assertNotEqual(code, 0, output)
        self.assertFalse((actual / '.venv').exists())

    def test_truncated_old_dotvenv_can_be_preserved_and_recreated(self):
        destination = self.root / 'project' / '.venv'
        destination.mkdir(parents=True)
        (destination / 'leftover.data').write_text('keep old incomplete environment', encoding='utf-8')
        code, output = self.run_tty(self.confirmed(
            f'jobs_python_prepare_venv {shlex.quote(str(destination))} 3.11 3.14 || exit $?'))
        self.assertEqual(code, 0, output)
        backups = list(destination.parent.glob('.venv.backup.*'))
        self.assertEqual(len(backups), 1, output)
        self.assertEqual((backups[0] / 'leftover.data').read_text(encoding='utf-8'),
                         'keep old incomplete environment')
        self.assertTrue((destination / 'bin/python').exists())

    def test_venv_creation_failure_keeps_complete_backup(self):
        destination = self.venv(version='3.9.6')
        code, output = self.run_tty(self.confirmed(f'jobs_python_prepare_venv {shlex.quote(str(destination))} 3.11 3.14 || exit $?'), b'\n', {'MOCK_VENV_FAIL': '1'})
        self.assertNotEqual(code, 0, output)
        backups = [path for path in destination.parent.iterdir() if path != destination and path.is_dir()]
        self.assertEqual(len(backups), 1, output)
        self.assertEqual((backups[0] / 'keep-me.txt').read_text(encoding='utf-8'), 'original user dependency and data')


if __name__ == '__main__':
    unittest.main(verbosity=2)
