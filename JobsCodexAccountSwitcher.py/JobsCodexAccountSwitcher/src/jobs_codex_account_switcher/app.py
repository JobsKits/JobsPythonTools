"""跨平台账户管理窗口。Created by Jobs."""
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
import argparse
from pathlib import Path
import sys
import shutil
import tempfile

from PySide6.QtCore import QLockFile, QSettings, QStandardPaths, Qt, QProcess, QProcessEnvironment, QThread, Signal
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFileDialog, QFormLayout,
                               QInputDialog, QMenu, QLabel, QLineEdit, QListWidget,
                               QListWidgetItem, QMessageBox, QPushButton, QVBoxLayout,
                               QWidget, QHBoxLayout)

from .core import FileSwitcher, Vault, identity
from .platforms import discover_apps, launch, require_stopped, close_app
from .appearance import apply_appearance


class SwitchWorker(QThread):
    completed = Signal(str)

    def __init__(self, engine, key, program, parent):
        super().__init__(parent)
        self.engine, self.key, self.program = engine, key, program

    def run(self):
        from .core import SwitchError
        try:
            close_app(self.program)
            self.engine.switch(self.key)
            launch(self.program)
            self.completed.emit('')
        except SwitchError as error:
            self.completed.emit(str(error))
        except Exception as error:
            self.completed.emit(f'{type(error).__name__}：自动切换未完成，请检查所选应用和当前账户。')


class Window(QWidget):
    def __init__(self, data_dir: Path, settings=None):
        super().__init__()
        self.data_dir = data_dir
        self.vault = None
        self.login_process = None
        self.switch_worker = None
        self.login_temp = None
        self.settings = settings if settings is not None else QSettings('Jobs', 'CodexAccountSwitcher')
        self.setWindowTitle('Jobs · Codex 账户切换器')
        self.resize(820, 610)
        self.setMinimumSize(650, 520)
        layout = QVBoxLayout(self)
        intro = QLabel('双击账户，自动关闭所选桌面应用、切换账户并重启。\n'
                       '首次添加仍需正常授权；切换后需在桌面应用核验账户。')
        intro.setWordWrap(True)
        heading = QHBoxLayout()
        heading.addWidget(intro, 1)
        self.appearance_slot = QHBoxLayout()
        heading.addLayout(self.appearance_slot)
        layout.addLayout(heading)
        form = QFormLayout()
        self.home = QLineEdit(self.settings.value('codex_home', os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))))
        form.addRow('Codex 数据目录', self.home)
        self.program = QLineEdit(self.settings.value('program', ''))
        if not self.program.text():
            apps = discover_apps()
            if apps:
                self.program.setText(str(apps[0]))
        program_row = QHBoxLayout()
        program_row.addWidget(self.program)
        choose = QPushButton('选择桌面应用')
        choose.clicked.connect(self.choose_program)
        program_row.addWidget(choose)
        form.addRow('重启的应用', program_row)
        candidate = shutil.which('codex') or ''
        if sys.platform == 'darwin':
            resources = Path(self.program.text()) / 'Contents/Resources'
            for relative in ('codex-cli/bin/codex', 'codex-cli/CodexCLI.app/Contents/MacOS/codex', 'codex-cli', 'codex'):
                bundled = resources / relative
                if bundled.is_file():
                    candidate = str(bundled)
                    break
        saved_cli = self.settings.value('cli', candidate)
        self.cli = QLineEdit(saved_cli if saved_cli and Path(saved_cli).is_file() else candidate)
        cli_row = QHBoxLayout()
        cli_row.addWidget(self.cli)
        cli_choose = QPushButton('选择 CLI 程序')
        cli_choose.clicked.connect(self.choose_cli)
        cli_row.addWidget(cli_choose)
        form.addRow('添加账户用 CLI', cli_row)
        self.theme = QComboBox()
        self.theme.addItems(['跟随系统', '白天', '黑夜'])
        self.theme.setCurrentIndex(int(self.settings.value('theme', 0)))
        self.theme.currentIndexChanged.connect(self.apply_theme)
        QApplication.instance().styleHints().colorSchemeChanged.connect(lambda _: self.apply_theme())
        self.theme.setToolTip('外观：跟随系统 / 白天 / 黑夜')
        self.theme.setAccessibleName('外观')
        self.theme.setFixedWidth(120)
        self.appearance_slot.addWidget(self.theme, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(form)
        self.password_protection = QCheckBox('启用口令保护（可选；关闭后账户库为本地明文）')
        self.password_protection.setEnabled(False)
        self.password_protection.toggled.connect(self.change_protection)
        layout.addWidget(self.password_protection)
        unlock = QPushButton('打开 / 解锁账户库')
        unlock.clicked.connect(lambda: self.execute(self.unlock))
        layout.addWidget(unlock)
        self.list = QListWidget()
        self.list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list.customContextMenuRequested.connect(self.account_menu)
        self.list.itemDoubleClicked.connect(lambda item: self.execute(lambda: self.switch_item(item)))
        self.list.setToolTip("双击账户切换；右键账户可切换或更改备注，右键空白处刷新缓存。")
        self.list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.list.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        layout.addWidget(self.list, 1)
        self.buttons = []
        for text, action in [('添加账户（独立浏览器授权）', self.enroll), ('保存当前登录账户', self.capture),
                             ('删除选中账户的本地保存', self.delete)]:
            button = QPushButton(text)
            button.clicked.connect(lambda checked=False, fn=action: self.execute(fn))
            button.setEnabled(False)
            layout.addWidget(button)
            self.buttons.append(button)
        self.status = QLabel('默认免口令使用；已加密的旧账户库需要原口令解锁。')
        self.status.setWordWrap(True)
        self.status.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.status)
        self.apply_theme()
        self.execute(self.open_without_password)

    def execute(self, action):
        """不展示底层异常正文，避免第三方异常包含凭据。"""
        from .core import SwitchError
        try:
            action()
        except SwitchError as error:
            QMessageBox.warning(self, '操作未完成', str(error))
        except Exception as error:
            QMessageBox.warning(self, '操作未完成', f'{type(error).__name__}：操作失败，未输出凭据。请检查当前登录账户，必要时完整退出 Codex 后选择原账户切换。')

    def engine(self):
        if not self.vault:
            from .core import SwitchError
            raise SwitchError('请先解锁账户库。')
        home = Path(self.home.text()).expanduser().absolute()
        self.settings.setValue('codex_home', str(home))
        self.settings.setValue('program', self.program.text())
        return FileSwitcher(home, self.vault, require_stopped)

    def selected(self):
        from .core import SwitchError
        item = self.list.currentItem()
        if not item:
            raise SwitchError('请选择账户。')
        return item.data(Qt.ItemDataRole.UserRole)

    def open_without_password(self):
        path = self.data_dir / 'accounts.enc'
        if Vault.needs_password(path):
            self.status.setText('该账户库已启用口令保护，请先解锁；解锁后可关闭口令保护。')
            return
        vault = Vault(path)
        if not path.exists():
            vault.save()
        self.activate_vault(vault)

    def activate_vault(self, vault):
        self.vault = vault
        for button in self.buttons:
            button.setEnabled(True)
        self.password_protection.setEnabled(True)
        self.sync_protection()
        self.refresh()

    def sync_protection(self):
        self.password_protection.blockSignals(True)
        self.password_protection.setChecked(bool(self.vault and self.vault.protected))
        self.password_protection.blockSignals(False)

    def unlock(self):
        if self.login_process:
            from .core import SwitchError
            raise SwitchError('先完成或取消正在进行的授权。')
        path = self.data_dir / 'accounts.enc'
        password = None
        if Vault.needs_password(path):
            password, ok = QInputDialog.getText(self, '解锁账户库', '输入原口令：', QLineEdit.EchoMode.Password)
            if not ok:
                return
        self.activate_vault(Vault(path, password))

    def change_protection(self, enabled):
        def change():
            from .core import SwitchError
            if self.login_process:
                raise SwitchError('先完成或取消正在进行的授权。')
            if not self.vault:
                raise SwitchError('先打开或解锁账户库。')
            password = None
            if enabled:
                password, ok = QInputDialog.getText(self, '启用口令保护', '设置口令（至少 12 字符）：', QLineEdit.EchoMode.Password)
                if not ok:
                    return
                again, ok = QInputDialog.getText(self, '确认口令', '再次输入：', QLineEdit.EchoMode.Password)
                if not ok:
                    return
                if password != again:
                    raise SwitchError('两次口令不一致。')
                if len(password) < 12:
                    raise SwitchError('启用口令保护时，口令至少 12 个字符。')
            self.vault.set_password(password)
            self.refresh()
        try:
            self.execute(change)
        finally:
            self.sync_protection()

    def refresh(self):
        self.list.clear()
        current = None
        home = Path(self.home.text()).expanduser()
        try:
            current = identity((home / 'auth.json').read_bytes())
        except Exception:
            pass
        if self.vault:
            for key, profile in self.vault.data['profiles'].items():
                suffix = ' · 当前缓存' if current and current['key'] == key else ''
                item = QListWidgetItem(f"{profile['label']} · {profile['email']}{suffix}")
                item.setData(Qt.ItemDataRole.UserRole, key)
                self.list.addItem(item)
            self.status.setText('账户库已打开。保存前请退出 Codex；双击切换会自动关闭并重启所选桌面应用。' +
                                '\n“当前缓存”仅代表本地文件身份，不代表桌面授权成功。' +
                                ('\n口令保护已开启。' if self.vault.protected else '\n口令保护未开启：账户库以明文保存。'))
        else:
            self.status.setText('账户库尚未解锁。检测到登录缓存。' if current else '账户库尚未解锁；未检测到受支持的登录缓存。')

    def choose_cli(self):
        path, _ = QFileDialog.getOpenFileName(self, '选择 codex CLI / codex-cli 可执行程序')
        if path:
            self.cli.setText(path)

    def enroll(self):
        """用独立 CODEX_HOME 授权，不登出正在使用的桌面账户。"""
        from .core import SwitchError
        if self.login_process:
            raise SwitchError('已有浏览器授权进行中。')
        cli = Path(self.cli.text()).expanduser()
        if not cli.is_file() or (sys.platform == 'win32' and cli.suffix.lower() != '.exe'):
            raise SwitchError('请选择原生 Codex CLI 可执行程序；Windows 需要 .exe，不能选择 npm 的 .cmd。')
        label, ok = QInputDialog.getText(self, '添加账户', '账户备注')
        if not ok or not label.strip():
            return
        self.settings.setValue('cli', str(cli))
        self.login_temp = tempfile.TemporaryDirectory(prefix='enroll-', dir=self.data_dir)
        process = QProcess(self)
        env = QProcessEnvironment.systemEnvironment()
        env.insert('CODEX_HOME', self.login_temp.name)
        for key in ('OPENAI_API_KEY', 'CODEX_API_KEY', 'CODEX_ACCESS_TOKEN'):
            env.remove(key)
        process.setProcessEnvironment(env)
        process.setProgram(str(cli))
        process.setArguments(['login', '-c', 'cli_auth_credentials_store="file"'])
        process.readyReadStandardOutput.connect(lambda: process.readAllStandardOutput())
        process.readyReadStandardError.connect(lambda: process.readAllStandardError())
        process.finished.connect(lambda code, state: self.finish_enrollment(label, code))
        process.errorOccurred.connect(lambda _: self.finish_enrollment(label, -1)
                                     if process.state() == QProcess.ProcessState.NotRunning else None)
        self.login_process = process
        self.status.setText('浏览器授权进行中，请选择正确账户；关闭窗口可取消。授权输出不记录到日志。')
        for button in self.buttons:
            button.setEnabled(False)
        process.start()

    def finish_enrollment(self, label, code):
        if not self.login_process:
            return
        process = self.login_process
        self.login_process = None
        def finish():
            from .core import SwitchError
            try:
                if code != 0:
                    raise SwitchError('浏览器授权未完成或 CLI 启动失败；当前桌面登录文件未修改。')
                raw = (Path(self.login_temp.name) / 'auth.json').read_bytes()
                self.vault.capture(label, raw)
            finally:
                self.login_temp.cleanup()
                self.login_temp = None
                process.deleteLater()
                for button in self.buttons:
                    button.setEnabled(True)
                self.refresh()
        self.execute(finish)

    def closeEvent(self, event):
        if self.switch_worker:
            event.ignore()
            return
        if self.login_process:
            if QMessageBox.question(self, '取消授权', '浏览器授权仍在进行，取消本次添加并关闭工具？') != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
            self.login_process.kill()
            self.login_process.waitForFinished(3000)
            if self.login_temp:
                self.login_temp.cleanup()
        event.accept()

    def account_menu(self, position):
        """右键命中的账户作为操作对象，空白处不显示菜单。"""
        item = self.list.itemAt(position)
        if self.login_process:
            return
        if item is None:
            menu = QMenu(self)
            action = menu.addAction('刷新缓存状态')
            action.triggered.connect(lambda checked=False: self.execute(self.refresh))
            menu.exec(self.list.viewport().mapToGlobal(position))
            return
        if self.vault is None:
            return
        self.list.setCurrentItem(item)
        key = item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self)
        switch_action = menu.addAction('切换账户并启动 Codex')
        switch_action.triggered.connect(lambda checked=False: self.execute(lambda: self.switch_item(item)))
        action = menu.addAction('更改备注')
        action.triggered.connect(lambda checked=False: self.execute(lambda: self.rename_account(key)))
        menu.addSeparator()
        refresh_action = menu.addAction('刷新缓存状态')
        refresh_action.triggered.connect(lambda checked=False: self.execute(self.refresh))
        menu.exec(self.list.viewport().mapToGlobal(position))

    def switch_item(self, item):
        """双击和右键使用同一账户目标及原有切换确认。"""
        from .core import SwitchError
        if self.login_process:
            raise SwitchError('先完成或取消正在进行的授权。')
        if not self.vault or item.listWidget() is not self.list:
            raise SwitchError('请选择已打开账户库中的账户。')
        self.list.setCurrentItem(item)
        self.switch()

    def rename_account(self, key):
        from .core import SwitchError
        if self.login_process:
            raise SwitchError('先完成或取消正在进行的授权。')
        if not self.vault or key not in self.vault.data['profiles']:
            raise SwitchError('目标账户不存在或账户库未解锁。')
        old = self.vault.data['profiles'][key]['label']
        label, ok = QInputDialog.getText(self, '更改备注', '账户备注', text=old)
        if not ok:
            return
        self.vault.rename(key, label)
        self.refresh()
        for index in range(self.list.count()):
            item = self.list.item(index)
            if item.data(Qt.ItemDataRole.UserRole) == key:
                self.list.setCurrentItem(item)
                break

    def capture(self):
        label, ok = QInputDialog.getText(self, '保存当前账户', '账户备注')
        if ok:
            self.engine().capture(label)
            self.refresh()

    def switch(self):
        from .core import SwitchError
        if self.switch_worker:
            raise SwitchError('账户切换正在进行。')
        key = self.selected()
        program = Path(self.program.text()).expanduser()
        if not program.exists() or program.suffix.lower() not in ('.app', '.exe'):
            raise SwitchError('先选择有效的桌面应用路径。')
        engine = self.engine()
        engine.check_storage()
        who = identity(engine.auth.read_bytes())
        if who['key'] == key:
            raise SwitchError('当前缓存已经是该账户，无需切换。')
        if who['key'] not in self.vault.data['profiles']:
            raise SwitchError('请先保存当前账户。')
        if QMessageBox.question(self, '切换账户', '将自动关闭所选 ChatGPT / Codex、保存最新登录态、切换账户并重启。\n正在运行的任务会被中断；应用无法正常退出时会清理其残留进程。继续？') != QMessageBox.StandardButton.Yes:
            return
        worker = SwitchWorker(engine, key, program, self)
        self.switch_worker = worker
        self.setEnabled(False)
        self.status.setText('正在关闭桌面应用、切换账户并重启，请稍候…')
        def complete(error):
            self.setEnabled(True)
            self.refresh()
            if error:
                QMessageBox.warning(self, '切换未完成', error)
        worker.completed.connect(complete)
        worker.finished.connect(self.switch_finished)
        worker.start()

    def switch_finished(self):
        worker = self.switch_worker
        self.switch_worker = None
        if worker:
            worker.deleteLater()

    def delete(self):
        from .core import SwitchError
        key = self.selected()
        if QMessageBox.question(self, '删除保存', '只删除本工具账户库内的保存，不登出或撤销账户。继续？') == QMessageBox.StandardButton.Yes:
            del self.vault.data['profiles'][key]
            self.vault.save()
            self.refresh()

    def choose_program(self):
        path, _ = QFileDialog.getOpenFileName(self, '选择 Codex 桌面应用', '/Applications' if sys.platform == 'darwin' else '',
                                             '应用 (*.app)' if sys.platform == 'darwin' else '应用 (*.exe)')
        if path:
            self.program.setText(path)

    def apply_theme(self):
        """账户窗口保存并应用三态主题。"""
        mode = self.theme.currentIndex()
        self.settings.setValue('theme', mode)
        apply_appearance(mode)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Jobs Codex 账户切换器')
    parser.add_argument('--codex-home', type=Path)
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    home = args.codex_home.expanduser().absolute() if args.codex_home is not None else None
    app = QApplication([sys.argv[0]])
    app.setStyle('Fusion')
    app.setOrganizationName('Jobs')
    app.setApplicationName('CodexAccountSwitcher')
    data_dir = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation))
    data_dir.mkdir(parents=True, exist_ok=True)
    lock = QLockFile(str(data_dir / 'instance.lock'))
    if not lock.tryLock(0):
        QMessageBox.warning(None, '已有实例', '账户切换器已经运行。')
        return 1
    window = Window(data_dir)
    if home is not None:
        window.home.setText(str(home))
    window.show()
    return app.exec()


if __name__ == '__main__':
    raise SystemExit(main())
