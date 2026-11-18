"""语言、主题和布局隔离回归。Created by Jobs on 2026年11月4日，星期三."""
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

import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
from PySide6.QtCore import QLocale, QRect, QSettings, QTimer, Qt
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication, QComboBox, QMessageBox, QPushButton, QStyle, QStyleOptionButton, QStyleOptionFrame
from jobs_ssh_key_mgr.app import Window, SetupWorker, ConnectionTestWorker
from jobs_ssh_key_mgr.core import Event, SetupError, SetupResult
from jobs_ssh_key_mgr.translations import LANGUAGE_NAMES, TR, resolve_language


class UiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setStyle('Fusion')

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.settings = QSettings(str(Path(self.temporary.name) / 'preferences.ini'), QSettings.Format.IniFormat)
        self.restore_patch = patch('jobs_ssh_key_mgr.app.find_existing_public_key', return_value=None)
        self.restore_patch.start()
        self.window = Window(settings=self.settings)
        self.window.show()
        self.app.processEvents()

    def tearDown(self):
        self.window.close()
        self.restore_patch.stop()
        self.temporary.cleanup()

    def test_reopening_restores_existing_public_key_for_copy_and_manual_test(self):
        result = SetupResult(Path('/test/.ssh/id_ed25519_personal'), 'ssh-ed25519 AAAA person@example.com', False)
        self.window.capture_result(result)
        self.window.finished()
        self.assertEqual(self.settings.value('last_key_name'), result.key.name)
        self.window.close()
        loader = Mock(return_value=result)
        generation = Mock(side_effect=AssertionError('startup must not generate or configure'))
        restored = Window(settings=self.settings, public_key_loader=loader, worker_factory=generation)
        try:
            self.assertEqual(restored.public_panel.content.toPlainText(), result.public_key)
            self.assertEqual(restored.public_panel.path.text(), str(result.key) + '.pub')
            self.assertTrue(restored.copy_button.isEnabled())
            self.assertTrue(restored.test_connection_button.isEnabled())
            self.assertEqual(restored.generate.text(), restored.text('regenerate'))
            self.assertFalse(restored.last_result.authenticated)
            self.assertEqual(loader.call_args.kwargs['preferred_name'], result.key.name)
            restored.copy_button.click()
            self.assertEqual(self.app.clipboard().text(), result.public_key)
            generation.assert_not_called()
            for language in TR:
                restored.language.setCurrentIndex(restored.language.findData(language))
                self.assertIn(restored.text('public_restored', path=str(result.key) + '.pub'), restored.output.toPlainText())
                self.assertEqual(restored.generate.text(), TR[language]['regenerate'])
        finally:
            restored.close()

    def test_unreadable_or_invalid_existing_public_key_leaves_safe_disabled_empty_state(self):
        for failure in (OSError('cannot read'), SetupError('public_file_invalid')):
            restored = Window(settings=self.settings, public_key_loader=Mock(side_effect=failure))
            try:
                self.assertFalse(restored.copy_button.isEnabled())
                self.assertFalse(restored.test_connection_button.isEnabled())
                self.assertIsNone(restored.last_result)
                self.assertEqual(restored.public_panel.content.toPlainText(), '')
                self.assertEqual(restored.events[-1].key, 'public_restore_failed')
            finally:
                restored.close()

    def test_all_languages_translate_the_entire_window_and_history(self):
        self.window.receive(Event('generated', {'path': '/test/key'}))
        for key in ('ssh_readme_created', 'ssh_readme_skipped'):
            self.window.receive(Event(key, {'path': '/test/.ssh/README.md'}))
        self.window.receive(Event('ssh_readme_failed', {'detail': 'E_SSH_README_WRITE'}))
        for language in TR:
            self.window.language.setCurrentIndex(self.window.language.findData(language))
            self.assertEqual(self.window.tokens.text(), TR[language]['open_tokens'])
            self.assertEqual(self.window.heading.text(), '🔑' + TR[language]['title'])
            self.assertIn(TR[language]['generated'].format(path='/test/key'), self.window.output.toPlainText())
            for key in ('ssh_readme_created', 'ssh_readme_skipped', 'ssh_readme_failed'):
                self.assertIn(TR[language][key].format(path='/test/.ssh/README.md', detail='E_SSH_README_WRITE'), self.window.output.toPlainText())
        self.assertEqual(len(LANGUAGE_NAMES), 11)

    def test_github_cli_failures_remain_distinct_when_history_language_changes(self):
        states = ('github_cli_missing', 'github_not_logged_in', 'github_auth_invalid',
                  'github_auth_forbidden', 'github_auth_network', 'github_auth_timeout',
                  'github_auth_check_failed')
        for key in states:
            self.window.receive(Event(key, {'detail': 'E_GH_AUTH_RESPONSE'} if key == 'github_auth_check_failed' else {}))
        for language, messages in TR.items():
            self.window.language.setCurrentIndex(self.window.language.findData(language))
            history = self.window.output.toPlainText()
            self.assertNotIn('github_auth_missing', messages)
            self.assertEqual(len({messages[key] for key in states}), len(states))
            for key in states:
                self.assertIn(messages[key].format(detail='E_GH_AUTH_RESPONSE'), history)

    def test_generate_row_and_four_icon_actions_with_conditional_copy(self):
        self.assertEqual(self.window.email.text(), '295060456@qq.com')
        actions = [self.window.copy_button, self.window.folder, self.window.github, self.window.tokens]
        self.assertEqual(self.window.action_buttons, actions)
        self.assertEqual(self.window.buttons, [self.window.generate, *actions])
        self.assertLess(self.window.generate.y(), self.window.copy_button.y())
        self.assertGreater(self.window.generate.width(), self.window.copy_button.width() * 1.9)
        self.assertEqual(self.window.copy_button.y(), self.window.folder.y())
        self.assertEqual(self.window.github.y(), self.window.tokens.y())
        self.assertLess(self.window.copy_button.y(), self.window.github.y())
        self.assertEqual(self.window.copy_button.x(), self.window.github.x())
        self.assertEqual(self.window.folder.x(), self.window.tokens.x())
        for button in actions:
            self.assertFalse(button.icon().isNull())
        self.assertFalse(hasattr(self.window, 'quit'))
        self.assertFalse(hasattr(self.window, 'view_public'))
        self.assertFalse(hasattr(self.window, 'public_window'))
        panel = self.window.public_panel
        self.assertTrue(panel.isVisible())
        self.assertIs(panel.copy_button, self.window.copy_button)
        self.assertIs(self.window.copy_button.parentWidget(), self.window)
        self.assertEqual(panel.content.toPlainText(), '')
        self.assertEqual(panel.content.placeholderText(), self.window.text('public_empty'))
        self.assertFalse(self.window.copy_button.isEnabled())
        self.assertFalse(self.window.test_connection_button.isEnabled())
        self.assertEqual(self.window.generate.text(), self.window.text('generate'))
        self.show_fake_public_result()
        self.assertTrue(self.window.copy_button.isEnabled())
        self.assertTrue(self.window.test_connection_button.isEnabled())
        self.assertEqual(self.window.generate.text(), self.window.text('regenerate'))

    def test_cancel_regeneration_preserves_public_result_preferences_and_history(self):
        result = self.show_fake_public_result()
        self.window.email.setText('changed@example.com')
        before_settings = {key: self.settings.value(key) for key in self.settings.allKeys()}
        before_history = self.window.output.toPlainText()
        before_status = self.window.public_panel.status.text()
        self.window.worker_factory = Mock(side_effect=AssertionError('cancel must not create worker'))
        with patch.object(self.window, 'confirm_regeneration', return_value=False) as confirmation:
            self.window.generate.click()
        confirmation.assert_called_once()
        self.window.worker_factory.assert_not_called()
        self.assertIs(self.window.last_result, result)
        self.assertEqual(self.window.public_panel.content.toPlainText(), result.public_key)
        self.assertEqual(self.window.output.toPlainText(), before_history)
        self.assertEqual(self.window.public_panel.status.text(), before_status)
        self.assertEqual({key: self.settings.value(key) for key in self.settings.allKeys()}, before_settings)
        self.assertTrue(self.window.copy_button.isEnabled())
        self.assertTrue(self.window.generate.isEnabled())
        self.assertIsNone(self.window.worker)

    def test_confirmed_regeneration_starts_once_and_busy_click_does_not_confirm_again(self):
        self.show_fake_public_result()
        self.window.worker_factory = Mock(return_value=Mock())
        with patch.object(self.window, 'confirm_regeneration', return_value=True) as confirmation, patch.object(self.window, 'launch_worker') as launch:
            self.window.start()
            self.window.start()
            confirmation.assert_called_once()
            self.window.worker_factory.assert_called_once()
            launch.assert_called_once()
        self.assertEqual(self.window.public_panel.content.toPlainText(), '')
        self.assertFalse(self.window.copy_button.isEnabled())
        self.window.worker = None

    def test_first_generation_does_not_show_regeneration_confirmation(self):
        self.window.worker_factory = Mock(return_value=Mock())
        with patch.object(self.window, 'confirm_regeneration', side_effect=AssertionError('no existing key')) as confirmation, patch.object(self.window, 'launch_worker'):
            self.window.start()
        confirmation.assert_not_called()
        self.window.worker_factory.assert_called_once()
        self.window.worker = None

    def test_regeneration_dialog_translates_and_defaults_to_cancel_in_both_themes(self):
        self.show_fake_public_result()
        for language, messages in TR.items():
            self.window.language.setCurrentIndex(self.window.language.findData(language))
            for mode in ('light', 'dark'):
                self.window.theme.setCurrentIndex(self.window.theme.findData(mode))
                for action in ('confirm', 'cancel', 'close'):
                    seen = {}
                    def respond():
                        dialog = self.app.activeModalWidget()
                        seen['dialog'] = isinstance(dialog, QMessageBox)
                        if not seen['dialog']:
                            return
                        seen['title'] = dialog.windowTitle()
                        seen['prompt'] = dialog.text()
                        seen['details'] = dialog.informativeText()
                        seen['default'] = dialog.defaultButton().text()
                        seen['escape'] = dialog.escapeButton().text()
                        seen['background'] = dialog.palette().color(QPalette.ColorRole.Window).lightness()
                        if action == 'close':
                            dialog.reject()
                        else:
                            role = QMessageBox.ButtonRole.AcceptRole if action == 'confirm' else QMessageBox.ButtonRole.RejectRole
                            next(button for button in dialog.buttons() if dialog.buttonRole(button) == role).click()
                    QTimer.singleShot(0, respond)
                    accepted = self.window.confirm_regeneration()
                    with self.subTest(language=language, theme=mode, action=action):
                        self.assertTrue(seen['dialog'])
                        self.assertEqual(accepted, action == 'confirm')
                        self.assertEqual(seen['prompt'], messages['regenerate_title'])
                        self.assertEqual(seen['details'], messages['regenerate_prompt'] + '\n\n' + messages['regenerate_details'].format(email=self.window.email.text().strip(), algorithm=self.window.algorithm.currentText()))
                        self.assertEqual(seen['default'], messages['cancel'])
                        self.assertEqual(seen['escape'], messages['cancel'])
                        self.assertEqual(seen['background'] < 128, mode == 'dark')

    def test_manual_theme_resists_system_changes_and_selection_persists(self):
        self.window.theme.setCurrentIndex(self.window.theme.findData('light'))
        self.window.language.setCurrentIndex(self.window.language.findData('fr'))
        self.app.styleHints().setColorScheme(Qt.ColorScheme.Dark)
        self.app.processEvents()
        self.assertGreater(self.app.palette().color(QPalette.ColorRole.Window).lightness(), 200)
        self.window.close()
        self.settings.setValue('email', 'saved-person@example.com')
        restored = Window(settings=self.settings)
        self.assertEqual(restored.email.text(), 'saved-person@example.com')
        self.assertEqual(restored.theme.currentData(), 'light')
        self.assertEqual(restored.language.currentData(), 'fr')
        restored.close()
        self.app.styleHints().setColorScheme(Qt.ColorScheme.Unknown)

    def test_system_theme_and_locale_mapping(self):
        self.window.theme.setCurrentIndex(self.window.theme.findData('system'))
        self.app.styleHints().setColorScheme(Qt.ColorScheme.Dark)
        self.window.system_theme_changed(Qt.ColorScheme.Dark)
        self.assertLess(self.app.palette().color(QPalette.ColorRole.Window).lightness(), 60)
        self.assertEqual(self.window.output.palette().color(QPalette.ColorRole.Base).name(), '#000000')
        self.assertEqual(self.window.public_panel.content.palette().color(QPalette.ColorRole.Text).name(), '#00ff00')
        self.app.styleHints().setColorScheme(Qt.ColorScheme.Light)
        self.window.system_theme_changed(Qt.ColorScheme.Light)
        self.assertGreater(self.app.palette().color(QPalette.ColorRole.Window).lightness(), 200)
        self.app.styleHints().setColorScheme(Qt.ColorScheme.Unknown)
        self.assertEqual(resolve_language('zh_HK'), 'zh_TW')
        self.assertEqual(resolve_language('bo_CN'), 'bo')
        self.assertEqual(resolve_language('ko_KR'), 'ko')

    def test_thread_remains_owned_until_finished(self):
        from PySide6.QtCore import QThread, Signal
        import time
        class DelayedWorker(QThread):
            event = Signal(object)
            completed = Signal(object)
            def __init__(self, email, algorithm, parent):
                super().__init__(parent)
            def run(self):
                self.completed.emit(None)
                time.sleep(0.15)
        self.window.worker_factory = DelayedWorker
        self.window.email.setText('person@example.com')
        self.window.start()
        time.sleep(0.03)
        self.app.processEvents()
        self.assertIsNotNone(self.window.worker)
        self.assertFalse(self.window.generate.isEnabled())
        self.window.close()
        self.assertTrue(self.window.isVisible())
        deadline = time.monotonic() + 3
        while self.window.worker is not None and time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(0.01)
        if self.window.worker is not None:
            self.window.worker.wait()
            self.app.processEvents()
        self.assertIsNone(self.window.worker)
        self.assertTrue(self.window.generate.isEnabled())

    def show_fake_public_result(self):
        result = SetupResult(Path('/test/id_ed25519_personal'),
                             'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAITestPublicKey person@example.com', False)
        self.window.pending_result = result
        self.window.finished()
        self.app.processEvents()
        return result

    def test_inline_public_panel_keeps_key_for_repeated_explicit_copy(self):
        clipboard = Mock()
        visible = {widget for widget in QApplication.topLevelWidgets() if widget.isVisible()}
        with patch('jobs_ssh_key_mgr.app.QApplication.clipboard', return_value=clipboard):
            result = self.show_fake_public_result()
            public = self.window.public_panel
            self.assertTrue(public.isVisible())
            self.assertFalse(public.isWindow())
            self.assertEqual({widget for widget in QApplication.topLevelWidgets() if widget.isVisible()}, visible)
            self.assertEqual(public.content.toPlainText(), result.public_key)
            self.assertEqual(public.path.text(), str(result.key) + '.pub')
            clipboard.setText.assert_not_called()
            public.copy_button.click()
            clipboard.setText.assert_called_once_with(result.public_key)
            public.copy_button.click()
            self.assertEqual(clipboard.setText.call_count, 2)
            self.assertEqual(public.status.text(), self.window.text('copy_success'))
            self.assertEqual(public.content.toPlainText(), result.public_key)

    def test_public_panel_follows_all_languages_and_theme(self):
        result = self.show_fake_public_result()
        public = self.window.public_panel
        with patch('jobs_ssh_key_mgr.app.QApplication.clipboard', return_value=Mock()):
            public.copy_button.click()
        for language, messages in TR.items():
            self.window.language.setCurrentIndex(self.window.language.findData(language))
            self.assertEqual(public.copy_button.text(), messages['copy_public'])
            self.assertEqual(public.heading.text(), messages['public_title'])
            self.assertEqual(public.content.accessibleName(), messages['public_content'])
            self.assertEqual(public.status.text(), messages['copy_success'])
            self.assertEqual(public.content.toPlainText(), result.public_key)
        self.window.theme.setCurrentIndex(self.window.theme.findData('dark'))
        self.assertEqual(public.content.palette().color(QPalette.ColorRole.Base).name(), '#000000')
        self.window.theme.setCurrentIndex(self.window.theme.findData('light'))
        self.assertEqual(public.content.palette().color(QPalette.ColorRole.Base).name(), '#ffffff')

    def test_private_key_text_is_never_displayed(self):
        self.window.pending_result = SetupResult(Path('/test/key'), '-----BEGIN OPENSSH PRIVATE KEY-----\nprivate-secret', False)
        self.window.finished()
        public = self.window.public_panel
        self.assertTrue(public.isVisible())
        self.assertEqual(public.content.toPlainText(), '')
        self.assertFalse(public.copy_button.isEnabled())
        self.assertNotIn('private-secret', self.window.output.toPlainText())
        self.assertIn('public_file_invalid', [event.key for event in self.window.events])

    def test_partial_setup_returns_public_key_after_configuration_error(self):
        result = SetupResult(Path('/test/key'), 'ssh-ed25519 AAAA person@example.com', False)
        engine = Mock(last_result=result)
        engine.execute.side_effect = SetupError('config_invalid')
        worker = SetupWorker('person@example.com', 'ed25519')
        worker.event.connect(self.window.receive)
        worker.completed.connect(self.window.capture_result)
        with patch('jobs_ssh_key_mgr.app.SshSetup', return_value=engine):
            worker.run()
        self.assertIs(self.window.pending_result, result)
        self.window.finished()
        self.assertTrue(self.window.public_panel.isVisible())
        self.assertEqual(self.window.public_panel.content.toPlainText(), result.public_key)
        self.assertIn('config_invalid', [event.key for event in self.window.events])

    def test_start_clears_old_public_key_in_the_persistent_panel(self):
        from PySide6.QtCore import QThread, Signal
        import time
        class DelayedWorker(QThread):
            event = Signal(object)
            completed = Signal(object)
            def __init__(self, email, algorithm, parent):
                super().__init__(parent)
            def run(self):
                time.sleep(0.05)
                self.completed.emit(None)
        self.show_fake_public_result()
        public = self.window.public_panel
        self.window.worker_factory = DelayedWorker
        with patch.object(self.window, 'confirm_regeneration', return_value=True):
            self.window.start()
        self.assertTrue(public.isVisible())
        self.assertEqual(public.content.toPlainText(), '')
        self.assertFalse(public.copy_button.isEnabled())
        deadline = time.monotonic() + 3
        while self.window.worker is not None and time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(0.01)
        if self.window.worker is not None:
            self.window.worker.wait()
            self.app.processEvents()
        self.assertIsNone(self.window.worker)
        self.assertFalse(public.copy_button.isEnabled())

    def test_recommendation_and_algorithm_explanation_follow_selection_and_language(self):
        for language, messages in TR.items():
            self.window.language.setCurrentIndex(self.window.language.findData(language))
            self.window.algorithm.setCurrentIndex(self.window.algorithm.findData('ed25519'))
            self.assertEqual(self.window.algorithm.currentText(), messages['algorithm_ed25519'])
            self.assertEqual(self.window.algorithm_description.text(), messages['algorithm_ed25519_description'])
            self.window.algorithm.setCurrentIndex(self.window.algorithm.findData('rsa'))
            self.assertEqual(self.window.algorithm.currentData(), 'rsa')
            self.assertEqual(self.window.algorithm_description.text(), messages['algorithm_rsa_description'])
            self.assertTrue(self.window.algorithm_description.isVisible())
            self.app.processEvents()
            self.assertGreaterEqual(self.window.generate.y(), self.window.terminal_splitter.y() + self.window.terminal_splitter.height() + 8)

    def test_algorithm_help_stays_compact_at_different_sizes_and_languages(self):
        for width, height in ((760, 710), (900, 760), (920, 1050)):
            for language in TR:
                self.window.language.setCurrentIndex(self.window.language.findData(language))
                for algorithm in ('ed25519', 'rsa'):
                    self.window.algorithm.setCurrentIndex(self.window.algorithm.findData(algorithm))
                    self.window.resize(width, height)
                    self.app.processEvents()
                    combo = self.window.algorithm
                    description = self.window.algorithm_description
                    combo_bottom = combo.mapTo(self.window, combo.rect().bottomLeft()).y() + 1
                    description_top = description.mapTo(self.window, description.rect().topLeft()).y()
                    with self.subTest(width=width, language=language, algorithm=algorithm):
                        self.assertEqual(description_top - combo_bottom, 6)
                        natural_height = description.fontMetrics().boundingRect(
                            QRect(0, 0, description.contentsRect().width(), 100000),
                            int(Qt.TextFlag.TextWordWrap), description.text()).height()
                        self.assertEqual(description.height(), max(description.fontMetrics().lineSpacing(), natural_height))
                        self.assertEqual(self.window.result_label.y() - description_top - description.height(), 18)
                        self.assertGreaterEqual(self.window.output.height(), 64)
                        self.assertGreaterEqual(self.window.public_panel.content.height(), 64)
                        self.assertGreaterEqual(self.window.generate.y(), self.window.terminal_splitter.y() + self.window.terminal_splitter.height() + 8)
            before = self.window.minimumHeight()
            for _ in range(4):
                self.window.resize(width, height)
                self.app.processEvents()
            self.assertEqual(self.window.minimumHeight(), before)

    def test_preferences_stay_small_at_top_right_beside_github_title(self):
        for width in (760, 900, 1100):
            for language, messages in TR.items():
                self.window.language.setCurrentIndex(self.window.language.findData(language))
                self.window.resize(width, 900)
                self.app.processEvents()
                with self.subTest(width=width, language=language):
                    self.assertIn('Jobs GitHub SSH', self.window.heading.text())
                    self.assertIn('SSH', self.window.windowTitle())
                    self.assertLessEqual(self.window.language.height(), 30)
                    self.assertLessEqual(self.window.theme.height(), 30)
                    self.assertLess(self.window.heading.geometry().right(), self.window.language.x())
                    self.assertEqual(self.window.language.y(), self.window.theme.y())
                    self.assertEqual(self.window.language.y(), self.window.layout().contentsMargins().top())
                    self.assertEqual(self.window.theme.geometry().right(), self.window.width() - 31)
                    self.assertEqual(self.window.language.accessibleName(), messages['language'])
                    self.assertEqual(self.window.theme.accessibleName(), messages['theme'])
                    self.assertLess(self.window.language.y(), self.window.email.y())
                    for button in self.window.action_buttons:
                        needed = button.fontMetrics().horizontalAdvance(button.text()) + button.iconSize().width() + 24
                        self.assertGreaterEqual(button.width(), needed)

    def test_preference_buttons_show_icons_and_select_checked_menu_actions(self):
        for button in (self.window.language, self.window.theme):
            self.assertIsInstance(button, QPushButton)
            self.assertNotIsInstance(button, QComboBox)
            self.assertIsNone(button.menu())
            self.assertFalse(button.icon().isNull())
            self.assertTrue(button.text())
            self.assertEqual(len(button.options_menu.actions()), button.count())
        french = self.window.language.options_menu.actions()[self.window.language.findData('fr')]
        french.trigger()
        self.assertEqual(self.window.language.currentData(), 'fr')
        self.assertEqual(self.settings.value('language'), 'fr')
        self.assertTrue(french.isChecked())
        self.assertEqual(self.window.language.text(), self.window.language.currentText())
        day_icon = self.window.theme.icon().cacheKey()
        dark = self.window.theme.options_menu.actions()[self.window.theme.findData('dark')]
        dark.trigger()
        self.assertEqual(self.window.theme.currentData(), 'dark')
        self.assertEqual(self.settings.value('theme'), 'dark')
        self.assertTrue(dark.isChecked())
        self.assertNotEqual(self.window.theme.icon().cacheKey(), day_icon)
        self.assertEqual(sum(action.isChecked() for action in self.window.theme.options_menu.actions()), 1)
        self.assertEqual(self.window.output.palette().color(QPalette.ColorRole.Base).name(), '#000000')

    def test_public_path_text_fits_current_font_style_and_language(self):
        field = self.window.public_panel.path
        for language in TR:
            self.window.language.setCurrentIndex(self.window.language.findData(language))
            for mode in ('light', 'dark'):
                self.window.theme.setCurrentIndex(self.window.theme.findData(mode))
                self.app.processEvents()
                option = QStyleOptionFrame()
                field.initStyleOption(option)
                contents = field.style().subElementRect(QStyle.SubElement.SE_LineEditContents, option, field)
                margins = field.textMargins()
                available = contents.height() - margins.top() - margins.bottom()
                with self.subTest(language=language, theme=mode):
                    self.assertGreaterEqual(available, field.fontMetrics().lineSpacing())
                    self.assertGreaterEqual(field.height(), field.minimumSizeHint().height())
                    self.assertEqual(field.placeholderText(), self.window.text('public_key_path', path='').strip())

    def test_connection_button_fits_its_icon_and_full_translation(self):
        button = self.window.test_connection_button
        for language in TR:
            self.window.language.setCurrentIndex(self.window.language.findData(language))
            for mode in ('light', 'dark'):
                self.window.theme.setCurrentIndex(self.window.theme.findData(mode))
                for enabled in (False, True):
                    button.setEnabled(enabled)
                    self.window.resize(self.window.minimumSize())
                    self.app.processEvents()
                    option = QStyleOptionButton()
                    button.initStyleOption(option)
                    contents = button.style().subElementRect(QStyle.SubElement.SE_PushButtonContents, option, button)
                    with self.subTest(language=language, theme=mode, enabled=enabled):
                        self.assertGreaterEqual(contents.height(), button.fontMetrics().lineSpacing())
                        self.assertFalse(button.icon().isNull())
                        self.assertGreaterEqual(contents.height(), button.iconSize().height())
                        needed_width = button.fontMetrics().horizontalAdvance(button.text()) + button.iconSize().width() + 4
                        self.assertGreaterEqual(contents.width(), needed_width)
                        self.assertEqual(button.text(), self.window.text('test_connection'))
                        self.assertLess(self.window.result_label.geometry().right(), button.x())
                        self.assertLess(button.geometry().bottom(), self.window.terminal_splitter.y())

    def test_token_button_opens_exact_tokens_page(self):
        with patch('jobs_ssh_key_mgr.app.QDesktopServices.openUrl', return_value=True) as opened:
            self.window.tokens.click()
            self.assertEqual(opened.call_args.args[0].toString(), 'https://github.com/settings/tokens')
        with patch('jobs_ssh_key_mgr.app.QDesktopServices.openUrl', return_value=False):
            self.window.tokens.click()
            self.assertEqual(self.window.events[-1].key, 'open_failed')
            self.assertEqual(self.window.events[-1].values['detail'], 'https://github.com/settings/tokens')

    def test_terminal_areas_are_readonly_scrollable_and_black_green_in_dark_mode(self):
        self.window.theme.setCurrentIndex(self.window.theme.findData('dark'))
        for terminal in (self.window.output, self.window.public_panel.content):
            terminal.setPlainText('\n'.join('line ' + str(index) for index in range(100)))
            self.assertTrue(terminal.isReadOnly())
            self.assertEqual(terminal.verticalScrollBarPolicy(), Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            self.assertEqual(terminal.palette().color(QPalette.ColorRole.Base).name(), '#000000')
            self.assertEqual(terminal.palette().color(QPalette.ColorRole.Text).name(), '#00ff00')
            self.assertNotEqual(terminal.palette().color(QPalette.ColorRole.Highlight).name(), terminal.palette().color(QPalette.ColorRole.HighlightedText).name())
        self.app.processEvents()
        self.assertGreater(self.window.output.verticalScrollBar().maximum(), 0)
        self.assertGreater(self.window.public_panel.content.verticalScrollBar().maximum(), 0)
        self.window.theme.setCurrentIndex(self.window.theme.findData('light'))
        self.assertEqual(self.window.output.palette().color(QPalette.ColorRole.Base).name(), '#ffffff')
        self.assertNotEqual(self.window.output.palette().color(QPalette.ColorRole.Text).name(), '#00ff00')

    def test_public_panel_sits_below_logs_without_hiding_buttons(self):
        for width,height in ((760,710),(900,760),(920,880)):
            self.window.resize(width,height)
            self.app.processEvents()
            output_bottom = self.window.output.mapTo(self.window,self.window.output.rect().bottomLeft()).y()
            public_top = self.window.public_panel.mapTo(self.window,self.window.public_panel.rect().topLeft()).y()
            self.assertGreater(public_top, output_bottom)
            self.assertGreater(self.window.generate.y(), self.window.terminal_splitter.geometry().bottom())
            self.assertLess(self.window.tokens.geometry().bottom(), self.window.height())
            self.assertTrue(self.window.public_panel.isVisible())

    def test_log_updates_keep_reader_scroll_position_and_follow_only_at_bottom(self):
        self.window.events = [Event('failed', {'detail': 'line ' + str(index)}) for index in range(100)]
        self.window.render_events()
        self.app.processEvents()
        scrollbar = self.window.output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum() // 3)
        position = scrollbar.value()
        self.window.receive(Event('failed', {'detail': 'new line'}))
        self.assertEqual(scrollbar.value(), position)
        self.assertLess(scrollbar.value(), scrollbar.maximum())
        scrollbar.setValue(scrollbar.maximum())
        self.window.receive(Event('failed', {'detail': 'follow line'}))
        self.assertEqual(scrollbar.value(), scrollbar.maximum())

    def test_standalone_connection_worker_verifies_and_completes_sourcetree_setup(self):
        result = SetupResult(Path('/test/key'), 'ssh-ed25519 AAAA person@example.com', False)
        tested = SetupResult(result.key, result.public_key, True, 'ExampleAccount')
        engine = Mock()
        engine.test_and_configure_sourcetree.return_value = tested
        worker = ConnectionTestWorker(result)
        received = []
        worker.completed.connect(received.append)
        with patch('jobs_ssh_key_mgr.app.SshSetup', return_value=engine):
            worker.run()
        engine.test_and_configure_sourcetree.assert_called_once_with(result)
        engine.execute.assert_not_called()
        self.assertEqual(received, [tested])
        engine.test_and_configure_sourcetree.side_effect = SetupError('public_file_invalid')
        failed = ConnectionTestWorker(result)
        retained = []
        failed.completed.connect(retained.append)
        with patch('jobs_ssh_key_mgr.app.SshSetup', return_value=engine):
            failed.run()
        self.assertEqual(retained[0].public_key, result.public_key)
        self.assertEqual(retained[0].key, result.key)
        self.assertFalse(retained[0].authenticated)

    def test_retest_keeps_public_key_and_does_not_restart_generation(self):
        from PySide6.QtCore import QThread, Signal
        import time
        result = self.show_fake_public_result()
        class TestWorker(QThread):
            event = Signal(object)
            completed = Signal(object)
            def __init__(self, value, parent):
                super().__init__(parent)
                self.value = value
            def run(self):
                self.event.emit(Event('testing_connection'))
                time.sleep(0.03)
                self.completed.emit(SetupResult(self.value.key, self.value.public_key, True, 'ExampleAccount'))
        self.window.test_worker_factory = TestWorker
        self.window.worker_factory = Mock(side_effect=AssertionError('must not generate on test'))
        self.window.test_connection_button.click()
        self.assertIsNotNone(self.window.worker)
        self.assertEqual(self.window.public_panel.content.toPlainText(), result.public_key)
        self.assertFalse(self.window.test_connection_button.isEnabled())
        self.assertTrue(self.window.copy_button.isEnabled())
        deadline = time.monotonic() + 3
        while self.window.worker is not None and time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(0.01)
        if self.window.worker is not None:
            self.window.worker.wait()
            self.app.processEvents()
        self.assertIsNone(self.window.worker)
        self.window.worker_factory.assert_not_called()
        self.assertTrue(self.window.last_result.authenticated)
        self.assertEqual(self.window.last_result.account, 'ExampleAccount')
        self.assertTrue(self.window.copy_button.isEnabled())
        self.assertTrue(self.window.test_connection_button.isEnabled())

    def test_default_email_is_real_editable_value_with_muted_theme_color(self):
        for theme,muted,normal,disabled in [('light','#52647d','#202c3d','#7a8494'),('dark','#a7b3c7','#edf1f7','#768298')]:
            self.window.theme.setCurrentIndex(self.window.theme.findData(theme))
            self.window.email.setText('295060456@qq.com')
            self.app.processEvents()
            self.assertEqual(self.window.email.text(),'295060456@qq.com')
            self.assertEqual(self.window.email.palette().color(QPalette.ColorRole.Text).name(),muted)
            self.assertEqual(self.window.email.objectName(),'defaultEmail')
            self.window.email.setText('another@example.com')
            self.app.processEvents()
            self.assertEqual(self.window.email.palette().color(QPalette.ColorRole.Text).name(),normal)
            self.window.email.setText('295060456@qq.com')
            self.window.email.setEnabled(False)
            self.app.processEvents()
            self.assertEqual(self.window.email.palette().color(QPalette.ColorGroup.Disabled,QPalette.ColorRole.Text).name(),disabled)
            self.window.email.setEnabled(True)
            self.window.email.selectAll()
            self.assertEqual(self.window.email.selectedText(),'295060456@qq.com')
            self.assertNotEqual(self.window.email.palette().color(QPalette.ColorRole.Highlight).name(),self.window.email.palette().color(QPalette.ColorRole.HighlightedText).name())
