# build.py | JobsHotspot
# Created by Jobs on 2026年11月5日，星期四.
"""Jobs Hotspot：本机生成 APP/DMG 或 EXE/ZIP。Created by Jobs.

运行先显示范围并等待回车；依赖缺失再次确认安装。只清理本工具固定 dist，
拒绝符号链接输出目录；成功后更新入口、打开产物位置并启动本次应用。
"""
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

import sys

# JOBS_INPUT_CHOICE_STYLE_BEGIN
# 仅渲染终端提示选项；输入、默认值、EOF 和取消继续由原调用负责。
import os as _jobs_prompt_os
import re as _jobs_prompt_re
import sys as _jobs_prompt_sys


"""Inlineable native Python URL display helpers; no I/O or environment mutation."""
import re as _jobs_url_re


# 只提取展示副本中的URL；查询、编码和配对括号保持原文。
def jobs_url_ranges(text):
    pattern = r'''[A-Za-z][A-Za-z0-9+.-]*://[^\s<>"'\x1b]+'''
    punctuation = '，。；：！？、（）【】《》「」『』“”‘’'
    result = []
    offset = 0
    while True:
        match = _jobs_url_re.search(pattern, text[offset:])
        if match is None:
            return result
        start = offset + match.start()
        url = match.group()
        for mark in punctuation:
            at = url.find(mark)
            if at >= 0:
                url = url[:at]
        while url:
            last = url[-1]
            unmatched = any(last == close and url.count(close) > url.count(opening)
                            for opening, close in (('(', ')'), ('[', ']'), ('{', '}')))
            if last in '.,;:!?' or unmatched:
                url = url[:-1]
            else:
                break
        result.append((start, start + len(url)))
        offset = start + len(url)


# 遮蔽地址，避免选项分段把URL路径中的Enter或查询分隔符当成询问语法。
def jobs_url_mask(text):
    output, tokens, offset, number = [], [], 0, 0
    for start, end in jobs_url_ranges(text):
        number += 1
        token = '\x02U' + str(number) + '\x03'
        while token in text:
            number += 1
            token = '\x02U' + str(number) + '\x03'
        output.extend((text[offset:start], token))
        tokens.append((token, text[start:end]))
        offset = end
    output.append(text[offset:])
    return ''.join(output), tokens


# 只给展示字符串着色，ANSI单独映射到可见字符，原上下文样式按顺序恢复。
def jobs_url_render(text, color=False):
    control = _jobs_url_re.compile(r'\x1b\][^\x1b\x07]*(?:\x07|\x1b\\)|\x1b\[[0-?]*[ -/]*[@-~]')
    sgr = _jobs_url_re.compile(r'\x1b\[[0-9;:]*m')
    value = control.sub(lambda match: match.group() if color and sgr.fullmatch(match.group()) else '', str(text))
    if not color:
        return value
    styles, pieces, length, offset = {}, [], 0, 0
    for match in sgr.finditer(value):
        part = value[offset:match.start()]
        pieces.append(part)
        length += len(part)
        styles[length] = styles.get(length, '') + match.group()
        offset = match.end()
    pieces.append(value[offset:])
    visible = ''.join(pieces)
    ranges = jobs_url_ranges(visible)
    starts = {start for start, _ in ranges}
    ends = {end - 1 for _, end in ranges}
    active, output, in_url = '', [], False
    for index in range(len(visible) + 1):
        if index in styles:
            tokens = styles[index]
            output.append(tokens)
            for match in sgr.finditer(tokens):
                token = match.group()
                fields = token[2:-1].split(';')
                reset, item = token == '\x1b[m', 0
                while item < len(fields):
                    field = fields[item]
                    if field == '0':
                        reset = True
                    if field in ('38', '48', '58') and item + 1 < len(fields):
                        mode = fields[item + 1]
                        item += 4 if mode == '2' else 2 if mode == '5' else 0
                    item += 1
                if reset:
                    active = ''
                active += token
            if in_url:
                output.append('\x1b[32;4m')
        if index == len(visible):
            break
        if index in starts:
            output.append('\x1b[32;4m')
            in_url = True
        output.append(visible[index])
        if index in ends:
            output.extend(('\x1b[0m', active))
            in_url = False
    return ''.join(output)


def jobs_prompt_render(text, stream=None, question=False):
    """显式询问突出青色题干；日志与普通展示仅保持原选项样式。"""
    stream = _jobs_prompt_sys.stdout if stream is None else stream
    plain = jobs_url_render(text, color=False)
    environment = _jobs_prompt_os.environ
    if ('NO_COLOR' in environment or not environment.get('TERM') or
            environment.get('TERM') == 'dumb' or environment.get('PLAIN_OUTPUT') == '1' or
            environment.get('IS_SOURCETREE_RUNTIME') == '1' or
            any(key.upper().startswith(('SOURCETREE', 'SOURCE_TREE')) for key in environment) or
            not _jobs_prompt_sys.stdin.isatty() or not stream.isatty()):
        return plain
    red = _jobs_prompt_re.compile(r'(?:输入)?(?:任意|任何)(?:非空)?(?:字符|内容|输入|键)|非空(?:字符|内容|输入)?|其它输入|其他输入|\bType (?:anything|any\S*)|\bPress any key', _jobs_prompt_re.I)
    green = _jobs_prompt_re.compile(r'(?:直接|仅|只需|只|按下|按)?\s*(?:回车|回車)|\b(?:Enter|Return)\b', _jobs_prompt_re.I)
    plain, url_tokens = jobs_url_mask(plain)
    if not question and not red.search(plain) and not green.search(plain):
        return jobs_url_render(text, color=True)

    def eligible_green(value):
        match = green.search(value)
        if match is None:
            return None
        prefix = _jobs_prompt_re.sub('[“”‘’「」『』\"\x27]', '', value[:match.start()])
        if _jobs_prompt_re.search(r'(?:空格|Space)\s*(?:后|再|并|then)?\s*$', prefix, _jobs_prompt_re.I):
            return None
        if _jobs_prompt_re.search(r'(?:输入|键入|填写|Type)[^；;|]*[A-Za-z0-9_+-]+\s*(?:后|再|并)?\s*$', prefix, _jobs_prompt_re.I):
            return None
        return match

    def segment(value, inherited=0, is_question=False):
        if not value:
            return value
        arbitrary, enter = red.search(value), eligible_green(value)
        if not inherited and arbitrary and enter and enter.start() < arbitrary.start():
            left, right = value[:arbitrary.start()], value[arbitrary.start():]
            connector = _jobs_prompt_re.search(r'(?:或者|或)\s*$', left)
            if connector:
                return segment(left[:connector.start()], 0, is_question) + connector.group() + segment(right, 31)
            return segment(left, 0, is_question) + segment(right, 31)
        if not inherited and arbitrary and enter and arbitrary.start() < enter.start():
            connector = _jobs_prompt_re.search(r'或\s*(?:直接|仅|只需|只|按下|按)?(?:回车|回車)', value)
            if connector:
                return segment(value[:connector.start()], 31, is_question) + '或' + segment(value[connector.start() + 1:])
        match = arbitrary or enter
        kind = inherited or (31 if arbitrary else 32 if enter else 0)
        if not kind:
            return ('\x1b[1;36m' + value + '\x1b[0m') if is_question and value.strip() else value
        start = 0 if inherited else match.start()
        prefix = value[:start]
        if is_question and prefix.strip():
            prefix = '\x1b[1;36m' + prefix + '\x1b[0m'
        return prefix + f'\x1b[1;{kind}m' + value[start:] + '\x1b[0m'

    output, inherited, depth, question_body = [], 0, 0, bool(question)
    parts = _jobs_prompt_re.split(r'([；;/|，,、？?：:=＝（）()\[\]【】\n])', plain)
    for index in range(0, len(parts), 2):
        part = parts[index]
        output.append(segment(part, inherited, question_body))
        if inherited or red.search(part) or eligible_green(part):
            question_body = False
        if index + 1 >= len(parts):
            break
        boundary = parts[index + 1]
        output.append(boundary)
        if boundary in '（([【':
            depth += 1
            inherited = 31 if red.search(part) else 32 if eligible_green(part) else inherited
        elif boundary in '）)]】':
            depth = max(0, depth - 1)
        elif boundary in '：:=＝':
            if not inherited:
                inherited = 31 if red.search(part) else 32 if eligible_green(part) else 0
        elif not depth:
            inherited = 0
    formatted = ''.join(output)
    for token, url in url_tokens:
        formatted = formatted.replace(token, url)
    return jobs_url_render(formatted, color=True)


def jobs_prompt_print(*values, sep=' ', end='\n', file=None, flush=False):
    stream = _jobs_prompt_sys.stdout if file is None else file
    print(jobs_prompt_render(sep.join(str(value) for value in values), stream), end=end, file=stream, flush=flush)
# JOBS_INPUT_CHOICE_STYLE_END


if sys.version_info < (3, 11):
    jobs_prompt_print('✖ 构建需要 Python 3.11+；请运行外层平台打包脚本自动检查运行时。', file=sys.stderr)
    raise SystemExit(1)

import argparse
from datetime import datetime
import hashlib
import json
import logging
import os
import platform
from pathlib import Path
import plistlib
import shutil
import subprocess
import tempfile
import tomllib
import venv
import zipfile

ROOT = Path(__file__).absolute().parents[2]
OUTER = ROOT.parent
NAME = 'JobsHotspot'
LOG_FILE = Path(tempfile.gettempdir()) / (NAME + '-build.log')
REQUIREMENTS = {
    'PySide6': ('PySide6>=6.8,<7', (6, 8), (7,)),
    'PyInstaller': ('PyInstaller>=6.22,<7', (6, 22), (7,)),
}


def configure_output():
    """Windows 终端/重定向统一 UTF-8，只影响当前构建进程。"""
    if sys.platform == 'win32':
        for stream in (sys.stdout, sys.stderr):
            if stream is not None and hasattr(stream, 'reconfigure'):
                stream.reconfigure(encoding='utf-8', errors='backslashreplace')


def confirm(message):
    """回车才继续；非空输入（包含空格）、EOF 和非终端全部停止。"""
    if not sys.stdin.isatty():
        raise RuntimeError('没有可交互输入，请在终端运行；尚未安装或清理。')
    try:
        answer = input(jobs_prompt_render(message + '（直接回车继续；输入任意字符或 Ctrl+C 取消）：', question=True))
    except EOFError as error:
        raise RuntimeError('输入已结束，已停止。') from error
    if answer != '':
        raise RuntimeError('已取消。')


def show_intro():
    """内层直接运行同样展示清理边界和依赖安装规则。"""
    jobs_prompt_print('Jobs Hotspot · 双端本机打包\n'
          '1、MacOS 生成独立 APP/DMG，Windows 生成 EXE 目录及 ZIP；不交叉编译。\n'
          '2、将删除当前工具外层 dist 的全部旧产物；不清理源码及其它应用。\n'
          '3、健康依赖直接复用；缺失时回车安装，任意非空输入（含空格）取消。\n'
          '4、输出 dist/YYYY.MM.DD HH-mm-ss；成功后更新第一层快捷方式。\n'
          '5、验证后打开本次产物位置，再启动本次 APP/EXE。\n'
          f'日志：{LOG_FILE}\n按 Ctrl+C 取消。', flush=True)


def child_environment():
    """只对子进程移除宿主 Qt / PyInstaller 注入，避免加载其它 APP 的运行库。"""
    environment = {key: value for key, value in os.environ.items()
                   if key not in ('QT_PLUGIN_PATH', 'QT_QPA_PLATFORM_PLUGIN_PATH')
                   and not key.startswith('_PYI_')}
    environment['PYTHONDONTWRITEBYTECODE'] = '1'
    environment['PYTHONUTF8'] = '1'
    environment['PYTHONIOENCODING'] = 'utf-8'
    return environment


def run(command, cwd=ROOT):
    """完整记录子进程输出，失败立即停止后续步骤。"""
    logging.info('执行：%s', subprocess.list2cmdline([str(item) for item in command]))
    with subprocess.Popen([str(item) for item in command], cwd=cwd,
                          env=child_environment(),
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          text=True, encoding='utf-8', errors='replace') as process:
        for line in process.stdout:
            jobs_prompt_print(line, end='', flush=True)
            logging.info('%s', line.rstrip())
        if process.wait() != 0:
            raise subprocess.CalledProcessError(process.returncode, command)


def fixed_directory(name):
    """仅允许工程既定 dist / work，拒绝外层及目标目录的链接改向。"""
    if (name not in ('dist', 'work') or ROOT.name != NAME or ROOT.parent != OUTER
            or OUTER.parent == OUTER):
        raise RuntimeError('构建目录布局异常，停止。')
    if (OUTER.is_symlink() or OUTER.absolute() != OUTER.resolve() or not OUTER.is_dir()
            or ROOT.is_symlink() or ROOT.absolute() != ROOT.resolve() or not ROOT.is_dir()):
        raise RuntimeError(f'交付根目录必须是真实目录：{OUTER}')
    target = OUTER / name
    if target.is_symlink() or target.resolve().parent != OUTER or (target.exists() and not target.is_dir()):
        raise RuntimeError(f'拒绝外部、符号链接或非目录输出：{target}')
    return target


def clean_dist(target):
    """清理仅接受本应用固定 dist；失败直接抛出，禁止继续构建。"""
    expected = fixed_directory('dist')
    if not str(target) or Path(target).absolute() != expected:
        raise RuntimeError(f'拒绝清理非固定 dist：{target}')
    if expected.exists():
        shutil.rmtree(expected)
    if expected.exists() or expected.is_symlink():
        raise RuntimeError(f'dist 清理失败：{expected}')


def missing_requirements(python):
    """在目标解释器内验证版本及关键 Qt 模块，避免仅凭文件存在判断健康。"""
    probe = '''import importlib, json
requirements = %r
missing = []
for name, (requirement, minimum, maximum) in requirements.items():
    try:
        module = importlib.import_module(name)
        version = tuple(int(part) for part in module.__version__.split('.')[:2])
        assert version >= minimum and (maximum is None or version < maximum)
        if name == 'PySide6':
            from PySide6 import QtCore, QtGui, QtWidgets, QtSvg
            assert hasattr(QtGui.QStyleHints, 'setColorScheme')
    except Exception:
        missing.append(requirement)
print(json.dumps(missing))
''' % REQUIREMENTS
    result = subprocess.run([str(python), '-c', probe], capture_output=True, env=child_environment(),
                            text=True, encoding='utf-8', errors='replace')
    if result.returncode:
        raise RuntimeError(f'构建 Python 无法运行：{python}\n{result.stderr}')
    return json.loads(result.stdout)


def managed_environment():
    """公共构建依赖按用户、Python 版本和架构管理，不夹带进源码。"""
    if sys.platform == 'win32':
        base = Path(os.environ.get('LOCALAPPDATA', str(Path.home() / 'AppData/Local')))
    else:
        base = Path.home() / 'Library/Caches'
    if not base.is_absolute() or base.resolve().is_relative_to(OUTER.resolve()):
        raise RuntimeError('用户级缓存位置无效或位于源码目录内，停止环境准备。')
    return base / 'JobsPythonTools/BuildEnvironments' / (
        NAME + f'-py{sys.version_info.major}.{sys.version_info.minor}-' + platform.machine())


def bootstrap():
    """依赖链：Python → 用户级 venv → pip → Qt/PyInstaller；只修复缺失层。"""
    current = Path(sys.executable)
    if not missing_requirements(current):
        jobs_prompt_print('✔ 复用当前解释器的健康构建依赖；不安装、不升级依赖。')
        return current
    environment = managed_environment()
    if (environment.is_symlink() or environment.absolute() != environment.resolve()
            or (environment.exists() and not environment.is_dir())):
        raise RuntimeError(f'拒绝修改符号链接或非目录构建环境：{environment}')
    if environment.exists() and not (environment / 'pyvenv.cfg').is_file():
        raise RuntimeError(f'环境目录未登记为 Python 虚拟环境，保留原内容并停止：{environment}')
    python = environment / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')
    healthy_python = False
    if python.exists():
        try:
            healthy_python = subprocess.run([str(python), '-c',
                                            'import sys; from pathlib import Path; assert sys.version_info >= (3,11); '
                                            'assert Path(sys.prefix).resolve() == Path(sys.argv[1]).resolve(); '
                                            'assert sys.prefix != sys.base_prefix', str(environment)],
                                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=child_environment()).returncode == 0
        except OSError:
            healthy_python = False
    missing = missing_requirements(python) if healthy_python else [item[0] for item in REQUIREMENTS.values()]
    if not missing:
        jobs_prompt_print(f'✔ 复用用户级健康构建环境：{environment}；不安装、不升级依赖。')
        return python
    jobs_prompt_print('缺少或不兼容的依赖：' + '、'.join(missing))
    jobs_prompt_print(f'来源：当前 pip 配置的软件源；依赖 {"、".join(missing)}；目标：{environment}')
    confirm('将在上述用户级构建环境安装必需依赖，不升级已有健康依赖')
    if not healthy_python:
        if environment.exists():
            backup = environment.with_name(environment.name + '.backup.' + datetime.now().strftime('%Y%m%d-%H%M%S') + '.' + str(os.getpid()))
            if backup.exists() or backup.is_symlink():
                raise RuntimeError(f'虚拟环境备份名称已被占用：{backup}')
            environment.rename(backup)
            jobs_prompt_print(f'ℹ 原虚拟环境已完整保留：{backup}')
        environment.parent.mkdir(parents=True, exist_ok=True)
        venv.EnvBuilder(with_pip=True).create(environment)
    pip = subprocess.run([str(python), '-m', 'pip', '--version'], capture_output=True, env=child_environment())
    if pip.returncode:
        run([python, '-m', 'ensurepip'])
    run([python, '-m', 'pip', '--version'])
    missing = missing_requirements(python)
    if missing:
        run([python, '-m', 'pip', 'install', '--disable-pip-version-check', *missing])
    remaining = missing_requirements(python)
    if remaining:
        raise RuntimeError('安装后依赖仍不可用，已停止：' + '、'.join(remaining))
    return python


def check_platform():
    """只允许本机平台构建，并在清理前检查必需系统命令。"""
    if sys.version_info < (3, 11) or sys.platform not in ('darwin', 'win32'):
        raise RuntimeError('请在 MacOS 或 Windows 使用 Python 3.11+ 运行。')
    commands = ('hdiutil', 'open') if sys.platform == 'darwin' else ('powershell.exe', 'explorer.exe')
    for command in commands:
        if not shutil.which(command):
            raise RuntimeError(f'缺少必需系统命令：{command}；尚未清理旧产物。')


def check_ui_resources():
    """图标与授权随源码提供，缺失时在清理旧产物前停止。"""
    folder = ROOT / 'src/jobs_hotspot/assets'
    platform_icon = 'app.icns' if sys.platform == 'darwin' else 'app.ico'
    for name in ('icon.png', platform_icon):
        path = folder / name
        if not path.is_file() or path.is_symlink() or path.stat().st_size == 0:
            raise RuntimeError(f'界面资源缺失或不是普通文件：{path}；尚未清理旧产物。')


def write_spec(work, version):
    """先在 spec 固定应用标识与窗口类型，避免修改签名后的 MacOS Info.plist。"""
    spec = work / (NAME + '.spec')
    text = f'''# Generated locally by Jobs Hotspot build.py.
import sys
a = Analysis([{str(ROOT / 'scripts/launch.py/launch.py')!r}], pathex=[{str(ROOT / 'src')!r}],
             binaries=[], datas=[({str(ROOT / 'src/jobs_hotspot/assets')!r}, 'jobs_hotspot/assets')],
             hiddenimports=['jobs_hotspot.backends.macos', 'jobs_hotspot.backends.windows'],
             hookspath=[], hooksconfig={{}},
             runtime_hooks=[], excludes=[], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name={NAME!r},
          debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
          console=False, disable_windowed_traceback=False, argv_emulation=False,
          icon={str(ROOT / 'src/jobs_hotspot/assets/app.ico')!r} if sys.platform == 'win32' else None,
          target_arch=None, codesign_identity=None, entitlements_file=None)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name={NAME!r})
'''
    if sys.platform == 'darwin':
        text += f'''app = BUNDLE(coll, name={NAME + '.app'!r}, icon={str(ROOT / 'src/jobs_hotspot/assets/app.icns')!r},
             bundle_identifier='com.jobs.hotspot',
             info_plist={{'LSUIElement': False, 'NSHighResolutionCapable': True,
                         'CFBundleDisplayName': 'Jobs Hotspot',
                         'NSAppleEventsUsageDescription': 'Control Internet Sharing in System Settings when you request a hotspot change.',
                         'CFBundleShortVersionString': {version!r}, 'CFBundleVersion': {version!r}}})
'''
    spec.write_text(text, encoding='utf-8')
    return spec


def validate_application(output):
    """检查可执行文件及 MacOS 应用配置，返回真实应用和可执行文件。"""
    if sys.platform == 'darwin':
        artifact = output / (NAME + '.app')
        executable = artifact / 'Contents/MacOS' / NAME
        with (artifact / 'Contents/Info.plist').open('rb') as stream:
            info = plistlib.load(stream)
        if info.get('LSUIElement') is not False or info.get('CFBundleIdentifier') != 'com.jobs.hotspot':
            raise RuntimeError('APP 应用配置或 Bundle ID 校验失败。')
        if not os.access(executable, os.X_OK):
            raise RuntimeError(f'APP 主程序不可执行：{executable}')
    else:
        artifact = executable = output / NAME / (NAME + '.exe')
        if not (artifact.parent / '_internal').is_dir():
            raise RuntimeError('Windows onedir 依赖目录未生成。')
    if not executable.is_file() or executable.stat().st_size == 0:
        raise RuntimeError(f'主程序未生成或为空：{executable}')
    with executable.open('rb') as stream:
        header = stream.read(4)
    if sys.platform == 'win32' and not header.startswith(b'MZ'):
        raise RuntimeError('生成的 Windows 主程序不是有效 EXE。')
    return artifact, executable


def package_application(output, artifact, work):
    """Mac 创建并验证 DMG；Windows 把完整 onedir 依赖打入 ZIP。"""
    if sys.platform == 'darwin':
        stage = work / 'dmg'
        stage.mkdir()
        shutil.copytree(artifact, stage / artifact.name, symlinks=True)
        (stage / 'Applications').symlink_to('/Applications', target_is_directory=True)
        package = output / (NAME + '.dmg')
        run(['hdiutil', 'create', '-volname', NAME, '-srcfolder', stage, '-format', 'UDZO', package])
        run(['hdiutil', 'verify', package])
    else:
        package = output / (NAME + '.zip')
        with zipfile.ZipFile(package, 'w', zipfile.ZIP_DEFLATED) as archive:
            for file in sorted(artifact.parent.rglob('*')):
                if file.is_file():
                    archive.write(file, file.relative_to(output))
        with zipfile.ZipFile(package) as archive:
            if archive.testzip() or f'{NAME}/{NAME}.exe' not in archive.namelist():
                raise RuntimeError('ZIP 完整性校验失败。')
    if not package.is_file() or package.stat().st_size == 0:
        raise RuntimeError(f'分发包未生成或为空：{package}')
    return package


def reveal_and_launch(output, artifact):
    """先打开本次磁盘位置，再启动本次生成的软件，不回退到旧包。"""
    if sys.platform == 'darwin':
        run(['open', output])
        run(['open', artifact])
    else:
        subprocess.Popen(['explorer.exe', str(output)], env=child_environment())
        subprocess.Popen([str(artifact)], cwd=artifact.parent, env=child_environment())


def smoke_application(executable):
    """成品无网络写操作的 GUI 冒烟通过后才发布快捷入口。"""
    environment = child_environment()
    environment['QT_QPA_PLATFORM'] = 'offscreen'
    result = subprocess.run([str(executable), '--smoke'], env=environment,
                            cwd=tempfile.gettempdir(), capture_output=True,
                            text=True, encoding='utf-8', errors='replace', timeout=45)
    logging.info('成品冒烟 stdout=%s stderr=%s', result.stdout, result.stderr)
    if result.returncode:
        raise RuntimeError(f'成品冒烟失败（{result.returncode}）：{result.stderr or result.stdout}')


def write_build_record(output, python, artifact, package):
    """记录实际构建环境及可分发文件摘要，便于跨机核验。"""
    probe = subprocess.run([str(python), '-c',
                            'import json,sys,PySide6,PyInstaller; '
                            'print(json.dumps({"python":sys.version,"PySide6":PySide6.__version__, '
                            '"PyInstaller":PyInstaller.__version__}))'],
                           capture_output=True, text=True, check=True, env=child_environment())
    record = json.loads(probe.stdout)
    with package.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    record.update(platform=platform.platform(), architecture=platform.machine(),
                  application=artifact.name, package=package.name,
                  package_sha256=digest,
                  signing='Local/ad-hoc build; no Developer ID notarization or Windows Authenticode signing',
                  hotspot_end_to_end='Not performed by builder')
    (output / 'build-info.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')


def build(python):
    """全部前置检查完成后清理，再生成、验证、发布和启动当次产物。"""
    sys.path.insert(0, str(ROOT / 'scripts' / 'artifact_shortcuts.py'))
    from artifact_shortcuts import clear_shortcuts, publish_shortcuts
    dist = fixed_directory('dist')
    work_root = fixed_directory('work')
    with (ROOT / 'pyproject.toml').open('rb') as stream:
        version = tomllib.load(stream)['project']['version']
    stamp = datetime.now().strftime('%Y.%m.%d %H-%M-%S')
    work = work_root / stamp
    if work.exists() or work.is_symlink():
        raise RuntimeError(f'构建工作目录已被占用，稍后重试：{work}')
    clear_shortcuts(OUTER)
    clean_dist(dist)
    output = dist / stamp
    output.mkdir(parents=True)
    work.mkdir(parents=True)
    spec = write_spec(work, version)
    run([python, '-m', 'PyInstaller', '--noconfirm', '--distpath', output,
         '--workpath', work / 'pyinstaller', spec])
    artifact, executable = validate_application(output)
    smoke_application(executable)
    package = package_application(output, artifact, work)
    write_build_record(output, python, artifact, package)
    publish_shortcuts(OUTER, [artifact, package])
    jobs_prompt_print(f'✔ 打包与校验成功：{output}', flush=True)
    reveal_and_launch(output, artifact)


def main():
    """help 无副作用；正常构建先确认，再创建日志及检查完整依赖链。"""
    configure_output()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepared', action='store_true',
                        help='只读验证当前解释器依赖；禁止安装依赖，仍保留构建确认')
    args = parser.parse_args()
    show_intro()
    confirm('已了解构建范围及旧产物删除')
    logging.basicConfig(filename=LOG_FILE, level=logging.INFO, encoding='utf-8',
                        format='%(asctime)s %(levelname)s %(message)s', force=True)
    check_platform()
    check_ui_resources()
    fixed_directory('dist')
    fixed_directory('work')
    if args.prepared:
        python = Path(sys.executable)
        missing = missing_requirements(python)
        if missing:
            raise RuntimeError('当前构建依赖不可用，--prepared 禁止安装：' + '、'.join(missing))
    else:
        python = bootstrap()
    build(python)
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        jobs_prompt_print('\n已取消。', file=sys.stderr)
        raise SystemExit(130)
    except Exception as error:
        if logging.getLogger().handlers:
            logging.exception('构建停止')
        jobs_prompt_print(f'✖ 构建停止：{error}\n日志：{LOG_FILE}', file=sys.stderr)
        raise SystemExit(1)
