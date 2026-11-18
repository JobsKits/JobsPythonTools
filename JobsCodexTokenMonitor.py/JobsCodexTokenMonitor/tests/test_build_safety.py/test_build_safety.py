"""构建中的删除边界、依赖取消和入口发布保护。Created by Jobs."""
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

import importlib.util
import ast
from contextlib import redirect_stdout
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[2] / 'scripts'


def load_script(name):
    """按文件位置加载构建辅助模块，测试不需要 Qt 或 PyInstaller。"""
    spec = importlib.util.spec_from_file_location('token_monitor_' + name, SCRIPTS / (name + '.py') / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build = load_script('build')
shortcuts = load_script('artifact_shortcuts')


class BuildSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name).resolve()
        self.outer = self.base / 'JobsCodexTokenMonitor.py'
        self.root = self.outer / 'JobsCodexTokenMonitor'
        self.root.mkdir(parents=True)
        self.root_patch = patch.object(build, 'ROOT', self.root)
        self.outer_patch = patch.object(build, 'OUTER', self.outer)
        self.root_patch.start()
        self.outer_patch.start()

    def tearDown(self):
        self.root_patch.stop()
        self.outer_patch.stop()
        self.temp.cleanup()

    def test_only_fixed_dist_can_be_deleted(self):
        outside = self.base / 'keep'
        outside.mkdir()
        sentinel = outside / 'important.txt'
        sentinel.write_text('keep', encoding='utf-8')
        for unsafe in ('', self.outer, self.root, outside, self.outer / 'work'):
            with self.subTest(path=unsafe), self.assertRaises(RuntimeError):
                build.clean_dist(unsafe)
        self.assertEqual(sentinel.read_text(encoding='utf-8'), 'keep')

    def test_clone_directory_can_have_any_name_including_spaces_and_chinese(self):
        for name in ('JobsCodexTokenMonitor', '我的监控 仓库'):
            with self.subTest(name=name):
                outer = self.base / name
                root = outer / 'JobsCodexTokenMonitor'
                root.mkdir(parents=True)
                with patch.object(build, 'ROOT', root), patch.object(build, 'OUTER', outer):
                    dist = outer / 'dist'
                    dist.mkdir()
                    (dist / 'old.app').write_text('old', encoding='utf-8')
                    self.assertEqual(build.fixed_directory('dist'), dist)
                    self.assertEqual(build.fixed_directory('work'), outer / 'work')
                    build.clean_dist(dist)
                    self.assertFalse(dist.exists())
                    self.assertTrue(root.is_dir())

    def test_actual_script_location_anchors_output_after_renaming_clone(self):
        outer = self.base / 'Gitee 监控'
        script = outer / 'JobsCodexTokenMonitor/scripts/build.py/build.py'
        script.parent.mkdir(parents=True)
        script.write_text(Path(build.__file__).read_text(encoding='utf-8'), encoding='utf-8')
        spec = importlib.util.spec_from_file_location('renamed_clone_build', script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.OUTER, outer)
        self.assertEqual(module.fixed_directory('dist'), outer / 'dist')

    def test_layout_and_filesystem_root_are_rejected(self):
        with patch.object(build, 'OUTER', self.base):
            with self.assertRaises(RuntimeError):
                build.fixed_directory('dist')
        with patch.object(build, 'OUTER', Path('/')), patch.object(build, 'ROOT', Path('/JobsCodexTokenMonitor')):
            with self.assertRaises(RuntimeError):
                build.fixed_directory('dist')
        with self.assertRaises(RuntimeError):
            build.fixed_directory('src')

    @unittest.skipIf(sys.platform == 'win32', 'Windows symlink privileges vary.')
    def test_linked_source_directory_is_rejected(self):
        outside = self.base / 'external-source'
        outside.mkdir()
        self.root.rmdir()
        self.root.symlink_to(outside, target_is_directory=True)
        with self.assertRaises(RuntimeError):
            build.fixed_directory('dist')

    @unittest.skipIf(sys.platform == 'win32', 'Windows symlink privileges vary.')
    def test_linked_dist_is_rejected_without_touching_target(self):
        outside = self.base / 'keep'
        outside.mkdir()
        (outside / 'important').write_text('keep', encoding='utf-8')
        (self.outer / 'dist').symlink_to(outside, target_is_directory=True)
        with self.assertRaises(RuntimeError):
            build.clean_dist(self.outer / 'dist')
        self.assertTrue((outside / 'important').is_file())
        with self.assertRaises(RuntimeError):
            shortcuts.clear_shortcuts(self.outer)

    @unittest.skipIf(sys.platform == 'win32', 'Windows symlink privileges vary.')
    def test_removing_dist_does_not_follow_internal_links(self):
        outside = self.base / 'keep'
        outside.mkdir()
        sentinel = outside / 'important'
        sentinel.write_text('keep', encoding='utf-8')
        dist = self.outer / 'dist'
        dist.mkdir()
        (dist / 'linked-app-framework').symlink_to(outside, target_is_directory=True)
        build.clean_dist(dist)
        self.assertFalse(dist.exists())
        self.assertTrue(sentinel.is_file())

    @unittest.skipIf(sys.platform == 'win32', 'Windows symlink privileges vary.')
    def test_work_symlink_is_rejected(self):
        outside = self.base / 'keep'
        outside.mkdir()
        (self.outer / 'work').symlink_to(outside, target_is_directory=True)
        with self.assertRaises(RuntimeError):
            build.fixed_directory('work')

    def test_cleanup_failure_stops(self):
        dist = self.outer / 'dist'
        dist.mkdir()
        with patch.object(build.shutil, 'rmtree', side_effect=PermissionError('denied')):
            with self.assertRaises(PermissionError):
                build.clean_dist(dist)
        self.assertTrue(dist.is_dir())

    def test_confirmation_rejects_space_eof_and_noninteractive(self):
        with patch.object(build.sys.stdin, 'isatty', return_value=True):
            with patch('builtins.input', return_value=' '), self.assertRaises(RuntimeError):
                build.confirm('test')
            with patch('builtins.input', side_effect=EOFError), self.assertRaises(RuntimeError):
                build.confirm('test')
        with patch.object(build.sys.stdin, 'isatty', return_value=False):
            with patch('builtins.input') as input_mock, self.assertRaises(RuntimeError):
                build.confirm('test')
            input_mock.assert_not_called()

    def test_current_healthy_interpreter_is_reused_without_writes(self):
        with redirect_stdout(io.StringIO()), patch.object(build, 'missing_requirements', return_value=[]):
            with patch.object(build.venv, 'EnvBuilder') as environment, patch.object(build, 'run') as run:
                self.assertEqual(build.bootstrap(), Path(sys.executable))
                environment.assert_not_called()
                run.assert_not_called()
                self.assertFalse((self.root / '.venv').exists())

    def test_windows_gbk_redirect_is_reconfigured_before_unicode_build_output(self):
        buffer = io.BytesIO()
        output = io.TextIOWrapper(buffer, encoding='gbk', errors='strict')
        try:
            with patch.object(build.sys, 'platform', 'win32'), patch.object(build.sys, 'stdout', output):
                build.configure_output()
                with patch.object(build, 'missing_requirements', return_value=[]):
                    self.assertEqual(build.bootstrap(), Path(sys.executable))
            output.flush()
            self.assertIn('✔ 复用当前解释器', buffer.getvalue().decode('utf-8'))
        finally:
            output.close()

    def test_main_prepares_output_before_help_without_build_mutation(self):
        with redirect_stdout(io.StringIO()), patch.object(build.sys, 'argv', ['build.py', '--help']):
            with patch.object(build, 'configure_output') as configure, patch.object(build, 'build') as actual_build:
                with self.assertRaises(SystemExit) as raised:
                    build.main()
                self.assertEqual(raised.exception.code, 0)
                configure.assert_called_once()
                actual_build.assert_not_called()

    def test_child_python_output_is_utf8_for_redirected_build_logs(self):
        with patch.dict(build.os.environ, {'PYTHONIOENCODING': 'gbk', 'PYTHONUTF8': '0'}):
            child = build.child_environment()
            self.assertEqual(child['PYTHONIOENCODING'], 'utf-8')
            self.assertEqual(child['PYTHONUTF8'], '1')
            self.assertEqual(build.os.environ['PYTHONIOENCODING'], 'gbk')

    def test_dependency_cancellation_precedes_environment_creation(self):
        with patch.object(build, 'missing_requirements', return_value=['PySide6>=6.8,<7']):
            with patch.object(build, 'confirm', side_effect=RuntimeError('cancelled')):
                with patch.object(build.venv, 'EnvBuilder') as environment, patch.object(build, 'run') as run:
                    with self.assertRaises(RuntimeError):
                        build.bootstrap()
                    environment.assert_not_called()
                    run.assert_not_called()
        self.assertFalse((self.outer / 'dist').exists())

    def test_main_missing_dependencies_never_clear_old_dist_before_confirmation(self):
        dist = self.outer / 'dist'
        dist.mkdir()
        sentinel = dist / 'keep.dmg'
        sentinel.write_text('old', encoding='utf-8')
        with patch.object(build.sys, 'argv', ['build.py']), patch.object(build, 'show_intro'):
            with patch.object(build, 'confirm', side_effect=[None, RuntimeError('cancelled')]):
                with patch.object(build.logging, 'basicConfig'), patch.object(build, 'check_platform'):
                    with patch.object(build, 'missing_requirements', return_value=['PySide6>=6.8,<7']):
                        with patch.object(build, 'build') as actual_build, self.assertRaises(RuntimeError):
                            build.main()
                        actual_build.assert_not_called()
        self.assertEqual(sentinel.read_text(encoding='utf-8'), 'old')

    def test_unsupported_platform_is_rejected_before_build(self):
        with patch.object(build.sys, 'platform', 'linux'), self.assertRaisesRegex(RuntimeError, 'macOS 或 Windows'):
            build.check_platform()

    def test_token_build_has_no_account_or_system_monitor_dependencies(self):
        self.assertEqual(set(build.REQUIREMENTS), {'PySide6', 'PyInstaller'})
        self.assertFalse(hasattr(build, 'create_token_launcher'))

    def test_pyinstaller_minimum_matches_project(self):
        requirement, minimum, _ = build.REQUIREMENTS['PyInstaller']
        self.assertEqual(requirement, 'PyInstaller>=6.10,<7')
        self.assertEqual(minimum, (6, 10))

    def test_direct_old_python_reports_version_requirement_before_tomllib_import(self):
        source = Path(build.__file__).read_text(encoding='utf-8')
        command = 'import sys; __file__ = ' + repr(build.__file__) + '; sys.version_info = (3, 9); exec(' + repr(source) + ')'
        result = subprocess.run([sys.executable, '-c', command], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('需要 Python 3.11+', result.stderr)
        self.assertNotIn('Traceback', result.stderr)
        self.assertNotIn('tomllib', result.stderr)

    def test_dependency_install_failure_stops_before_recheck(self):
        python = self.root / '.venv' / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')
        python.parent.mkdir(parents=True)
        python.touch()
        with patch.object(build, 'missing_requirements', return_value=['PySide6>=6.8,<7']) as probe:
            with patch.object(build, 'confirm'), patch.object(build.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0)):
                with patch.object(build, 'run', side_effect=[None, subprocess.CalledProcessError(1, 'pip')]):
                    with self.assertRaises(subprocess.CalledProcessError):
                        build.bootstrap()
        self.assertEqual(probe.call_count, 3)
        self.assertFalse((self.outer / 'dist').exists())

    def test_dependency_postinstall_failure_is_blocking(self):
        python = self.root / '.venv' / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')
        python.parent.mkdir(parents=True)
        python.touch()
        with patch.object(build, 'missing_requirements', return_value=['PySide6>=6.8,<7']) as probe:
            with patch.object(build, 'confirm'), patch.object(build.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0)):
                with patch.object(build, 'run'), self.assertRaisesRegex(RuntimeError, '安装后依赖仍不可用'):
                    build.bootstrap()
        self.assertEqual(probe.call_count, 4)
        self.assertFalse((self.outer / 'dist').exists())

    @unittest.skipIf(sys.platform == 'win32', 'macOS relative-link behavior.')
    def test_relative_shortcuts_and_selective_cleanup(self):
        dist = self.outer / 'dist' / '2026.10.15 12-30-00'
        dist.mkdir(parents=True)
        app = dist / 'JobsCodexTokenMonitor.app'
        app.mkdir()
        package = dist / 'JobsCodexTokenMonitor.dmg'
        package.write_text('dmg', encoding='utf-8')
        unrelated = self.outer / 'Unrelated.app'
        unrelated.symlink_to(self.base / 'elsewhere', target_is_directory=True)
        real = self.outer / 'Keep.dmg'
        real.write_text('keep', encoding='utf-8')
        shortcuts.publish_shortcuts(self.outer, [app, package])
        entry = self.outer / app.name
        self.assertFalse(entry.readlink().is_absolute())
        self.assertEqual(entry.resolve(), app)
        shortcuts.clear_shortcuts(self.outer)
        self.assertFalse(entry.is_symlink())
        self.assertTrue(unrelated.is_symlink())
        self.assertEqual(real.read_text(encoding='utf-8'), 'keep')

    @unittest.skipIf(sys.platform == 'win32', 'macOS relative-link behavior.')
    def test_publication_preflights_all_name_collisions(self):
        dist = self.outer / 'dist' / '2026.10.15 12-30-00'
        dist.mkdir(parents=True)
        app = dist / 'JobsCodexTokenMonitor.app'
        app.mkdir()
        package = dist / 'JobsCodexTokenMonitor.dmg'
        package.write_text('new', encoding='utf-8')
        occupied = self.outer / package.name
        occupied.write_text('do not overwrite', encoding='utf-8')
        with self.assertRaises(RuntimeError):
            shortcuts.publish_shortcuts(self.outer, [app, package])
        self.assertFalse((self.outer / app.name).is_symlink())
        self.assertEqual(occupied.read_text(encoding='utf-8'), 'do not overwrite')

    def test_windows_zip_contains_complete_onedir_runtime(self):
        output = self.outer / 'dist' / '2026.10.15 12-30-00'
        app_dir = output / 'JobsCodexTokenMonitor'
        runtime = app_dir / '_internal'
        runtime.mkdir(parents=True)
        artifact = app_dir / 'JobsCodexTokenMonitor.exe'
        artifact.write_bytes(b'MZtest')
        (runtime / 'runtime.dll').write_bytes(b'test')
        with patch.object(build.sys, 'platform', 'win32'):
            package = build.package_application(output, artifact, self.outer / 'work')
        with build.zipfile.ZipFile(package) as archive:
            self.assertIn('JobsCodexTokenMonitor/JobsCodexTokenMonitor.exe', archive.namelist())
            self.assertIn('JobsCodexTokenMonitor/_internal/runtime.dll', archive.namelist())


    def test_prepared_mode_requires_healthy_dependencies_without_install_or_cleanup(self):
        dist = self.outer / 'dist'
        dist.mkdir()
        sentinel = dist / 'keep.dmg'
        sentinel.write_text('old', encoding='utf-8')
        with patch.object(build.sys, 'argv', ['build.py', '--prepared']):
            with patch.object(build, 'show_intro'), patch.object(build, 'confirm') as confirm:
                with patch.object(build.logging, 'basicConfig'), patch.object(build, 'check_platform'):
                    with patch.object(build, 'missing_requirements', return_value=['PySide6>=6.8,<7']):
                        with patch.object(build, 'bootstrap') as bootstrap, patch.object(build, 'build') as actual:
                            with self.assertRaisesRegex(RuntimeError, '--prepared 禁止安装'):
                                build.main()
                            bootstrap.assert_not_called()
                            actual.assert_not_called()
                            confirm.assert_called_once()
        self.assertEqual(sentinel.read_text(encoding='utf-8'), 'old')

    def test_prepared_mode_reuses_current_interpreter_after_confirmation(self):
        with patch.object(build.sys, 'argv', ['build.py', '--prepared']):
            with patch.object(build, 'show_intro'), patch.object(build, 'confirm') as confirm:
                with patch.object(build.logging, 'basicConfig'), patch.object(build, 'check_platform'):
                    with patch.object(build, 'missing_requirements', return_value=[]):
                        with patch.object(build, 'bootstrap') as bootstrap, patch.object(build, 'build') as actual:
                            self.assertEqual(build.main(), 0)
                            bootstrap.assert_not_called()
                            actual.assert_called_once_with(Path(sys.executable))
                            confirm.assert_called_once()

    def test_fixed_dist_non_directory_is_rejected(self):
        target = self.outer / 'dist'
        target.write_text('keep', encoding='utf-8')
        with self.assertRaises(RuntimeError):
            build.clean_dist(target)
        self.assertEqual(target.read_text(encoding='utf-8'), 'keep')

    def test_windows_launch_has_no_monitor_or_account_switch_mode_argument(self):
        output = self.outer / 'dist' / '2026.10.18 12-30-00'
        artifact = output / build.NAME / (build.NAME + '.exe')
        with patch.object(build.sys, 'platform', 'win32'), patch.object(build.subprocess, 'Popen') as process:
            build.reveal_and_launch(output, artifact)
        self.assertEqual(process.call_args_list[0].args[0], ['explorer.exe', str(output)])
        self.assertEqual(process.call_args_list[1].args[0], [str(artifact)])
        self.assertEqual(process.call_args_list[1].kwargs['cwd'], artifact.parent)

    def test_spec_embeds_local_icon_and_stable_identity(self):
        icon = self.outer / 'icon.png'
        icon.write_bytes(b'local icon')
        work = self.outer / 'work'
        work.mkdir()
        with patch.object(build.sys, 'platform', 'darwin'):
            spec = build.write_spec(work, '0.3.0')
        text = spec.read_text(encoding='utf-8')
        tree = ast.parse(text)
        analysis = next(node for node in ast.walk(tree)
                        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                        and node.func.id == 'Analysis')
        self.assertEqual(ast.literal_eval(analysis.args[0]), [str(self.root / 'scripts/launch.py/launch.py')])
        datas = next(keyword.value for keyword in analysis.keywords if keyword.arg == 'datas')
        self.assertEqual(ast.literal_eval(datas), [(str(icon), 'assets')])
        self.assertIn(build.NAME + '.app', text)
        self.assertNotIn('create_token_launcher', text)



    def test_child_environment_removes_host_qt_and_frozen_app_paths(self):
        incoming = {'QT_PLUGIN_PATH': '/old/app/plugins',
                    'QT_QPA_PLATFORM_PLUGIN_PATH': '/old/app/platforms',
                    '_PYI_APPLICATION_HOME_DIR': '/old/app', '_PYI_PARENT_PROCESS_LEVEL': '1',
                    'JOBS_KEEP_SETTING': 'unchanged'}
        with patch.dict(build.os.environ, incoming, clear=True):
            child = build.child_environment()
            self.assertNotIn('QT_PLUGIN_PATH', child)
            self.assertNotIn('QT_QPA_PLATFORM_PLUGIN_PATH', child)
            self.assertFalse(any(key.startswith('_PYI_') for key in child))
            self.assertEqual(child['JOBS_KEEP_SETTING'], 'unchanged')
            self.assertEqual(build.os.environ['QT_PLUGIN_PATH'], '/old/app/plugins')


if __name__ == '__main__':
    unittest.main()
