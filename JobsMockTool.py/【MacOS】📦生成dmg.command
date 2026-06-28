#!/bin/zsh
# 脚本自述：
# - 脚本名称：【MacOS】📦生成dmg.command
# - 核心用途：构建 JobsMockTool.app，并生成可安装的 DMG。
# - 影响范围：会在内层 JobsMockTool/.venv、build、dist 中安装依赖、清理旧产物并生成新安装包。
# - 运行提示：运行后会先打印内置自述；终端模式按回车确认后继续，按 Ctrl+C 可取消。

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-${(%):-%x}}")" && pwd)"
SCRIPT_PATH="${SCRIPT_DIR}/$(basename -- "$0")"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/JobsMockTool" && pwd -P)"
SCRIPT_BASENAME=$(basename "$0" | sed 's/\.[^.]*$//')
LOG_FILE="${TMPDIR:-/tmp}/${SCRIPT_BASENAME}.log"

VENV_DIR="${PROJECT_ROOT}/.venv"
BUILD_DIR="${PROJECT_ROOT}/build"
DIST_DIR="${PROJECT_ROOT}/dist"
APP_BUNDLE="${DIST_DIR}/JobsMockTool.app"
DMG_PATH="${DIST_DIR}/JobsMockTool-Installer.dmg"
DMG_STAGING="${DIST_DIR}/dmg_staging"
# 按当前输出级别记录终端信息，并同步写入脚本日志。
log()            { echo -e "$1" | tee -a "$LOG_FILE"; }
# 按当前输出级别记录终端信息，并同步写入脚本日志。
color_echo()     { log "\033[1;32m$1\033[0m"; }
# 按当前输出级别记录终端信息，并同步写入脚本日志。
info_echo()      { log "\033[1;34mℹ $1\033[0m"; }
# 按当前输出级别记录终端信息，并同步写入脚本日志。
success_echo()   { log "\033[1;32m✔ $1\033[0m"; }
# 按当前输出级别记录终端信息，并同步写入脚本日志。
warn_echo()      { log "\033[1;33m⚠ $1\033[0m"; }
# 按当前输出级别记录终端信息，并同步写入脚本日志。
warm_echo()      { log "\033[1;33m$1\033[0m"; }
# 按当前输出级别记录终端信息，并同步写入脚本日志。
note_echo()      { log "\033[1;35m➤ $1\033[0m"; }
# 按当前输出级别记录终端信息，并同步写入脚本日志。
error_echo()     { log "\033[1;31m✖ $1\033[0m"; }
# 按当前输出级别记录终端信息，并同步写入脚本日志。
err_echo()       { log "\033[1;31m$1\033[0m"; }
# 按当前输出级别记录终端信息，并同步写入脚本日志。
debug_echo()     { log "\033[1;35m🐞 $1\033[0m"; }
# 按当前输出级别记录终端信息，并同步写入脚本日志。
highlight_echo() { log "\033[1;36m🔹 $1\033[0m"; }
# 按当前输出级别记录终端信息，并同步写入脚本日志。
gray_echo()      { log "\033[0;90m$1\033[0m"; }
# 按当前输出级别记录终端信息，并同步写入脚本日志。
bold_echo()      { log "\033[1m$1\033[0m"; }
# 按当前输出级别记录终端信息，并同步写入脚本日志。
underline_echo() { log "\033[4m$1\033[0m"; }
# 同步显示命令输出并写入日志，失败状态由 pipefail 原样向上返回。
run_logged() {
  "$@" 2>&1 | tee -a "$LOG_FILE"
}
# 打印写死在脚本内部的自述，避免运行时依赖外部 README。
show_script_intro_and_wait() {
  clear
  print -r -- '============================== 脚本内置自述 =============================='
  print -r -- "脚本名称：${SCRIPT_PATH}"
  print -r -- '核心用途：构建 JobsMockTool.app，并生成可安装的 DMG。'
  print -r -- '影响范围：会在内层 JobsMockTool/.venv、build、dist 中安装依赖、清理旧产物并生成新安装包。'
  print -r -- '取消方式：确认前按 Ctrl+C 终止，不会继续执行后续业务。'
  print -r -- "日志位置：${LOG_FILE}"
  print -r -- '============================================================================'
  echo ""
  read -r "?👉 已了解脚本用途与影响，按回车继续；按 Ctrl+C 取消：" _
}
# 普通升级动作默认跳过，只有输入任意字符后才执行。
ask_any_to_run() {
  local message="$1"
  local answer=""
  read -r "?${message}（直接回车跳过；输入任意字符后回车执行）：" answer
  [[ -n "$answer" ]]
}
# 清理旧产物属于破坏性动作，必须输入 YES 才允许继续。
confirm_yes() {
  echo ""
  warn_echo "$1"
  gray_echo "危险操作必须输入 YES 后回车；其它输入一律取消。"
  local input=""
  IFS= read -r "input?➤ "
  [[ "$input" == "YES" ]]
}
# 检查 macOS、系统工具和项目输入文件，失败时给出明确目标。
check_environment() {
  if [[ "$(uname -s)" != "Darwin" ]]; then
    error_echo "该脚本只支持 macOS。"
    return 1
  fi

  local command_name=""
  for command_name in python3 hdiutil; do
    if ! command -v "$command_name" >/dev/null 2>&1; then
      error_echo "未找到命令：${command_name}。请先补齐 macOS 构建环境。"
      return 1
    fi
  done

  local required_file=""
  for required_file in app.py requirements.txt; do
    if [[ ! -f "${PROJECT_ROOT}/${required_file}" ]]; then
      error_echo "缺少项目文件：${PROJECT_ROOT}/${required_file}"
      return 1
    fi
  done

  info_echo "Python：$(python3 --version 2>&1)"
  info_echo "项目目录：${PROJECT_ROOT}"
  info_echo "日志文件：${LOG_FILE}"
}
# 创建项目虚拟环境，并按需升级 pip 后安装构建依赖。
prepare_python_environment() {
  info_echo "创建 / 复用虚拟环境：${VENV_DIR}"
  run_logged python3 -m venv "$VENV_DIR"
  source "${VENV_DIR}/bin/activate"

  if ask_any_to_run "是否升级虚拟环境中的 pip？"; then
    info_echo "升级 pip"
    run_logged python -m pip install --upgrade pip
  else
    gray_echo "已跳过 pip 升级。"
  fi

  info_echo "安装 requirements.txt 中的构建依赖"
  run_logged python -m pip install -r "${PROJECT_ROOT}/requirements.txt"
}
# 清理两端共用的 PyInstaller 构建目录，避免旧文件污染本次产物。
clean_build_outputs() {
  if ! confirm_yes "即将删除旧构建目录：${BUILD_DIR} 和 ${DIST_DIR}"; then
    warn_echo "未收到 YES，已取消本次构建。"
    return 1
  fi

  info_echo "清理旧构建产物"
  rm -rf -- "$BUILD_DIR" "$DIST_DIR"
}
# 使用 PyInstaller 生成 macOS App Bundle。
build_macos_app() {
  info_echo "开始构建 macOS App；QtWebEngine 体积较大，请耐心等待。"
  run_logged pyinstaller \
    --noconfirm \
    --clean \
    --windowed \
    --onedir \
    --name "JobsMockTool" \
    --osx-bundle-identifier "com.jobs.mocktool" \
    --collect-all PySide6 \
    "${PROJECT_ROOT}/app.py"

  if [[ ! -d "$APP_BUNDLE" ]]; then
    error_echo "未找到 App Bundle：${APP_BUNDLE}"
    return 1
  fi
  success_echo "macOS App 构建完成：${APP_BUNDLE}"
}
# 生成带 Applications 快捷入口的拖拽安装 DMG。
build_dmg_installer() {
  info_echo "准备 DMG 临时目录：${DMG_STAGING}"
  rm -rf -- "$DMG_STAGING"
  mkdir -p "$DMG_STAGING"
  cp -R "$APP_BUNDLE" "$DMG_STAGING/"
  ln -s /Applications "$DMG_STAGING/Applications"

  info_echo "生成 DMG 安装包"
  run_logged hdiutil create \
    -volname "JobsMockTool Installer" \
    -srcfolder "$DMG_STAGING" \
    -ov \
    -format UDZO \
    "$DMG_PATH"

  rm -rf -- "$DMG_STAGING"
  success_echo "macOS DMG 构建完成：${DMG_PATH}"
}
# 汇总输出产物、Gatekeeper 提示和排查日志位置。
show_build_result() {
  echo ""
  highlight_echo "============================== 构建完成 =============================="
  success_echo "App：${APP_BUNDLE}"
  success_echo "DMG：${DMG_PATH}"
  warn_echo "首次打开如被 Gatekeeper 拦截：系统设置 -> 隐私与安全性 -> 仍要打开。"
  info_echo "完整日志：${LOG_FILE}"
  highlight_echo "========================================================================"
}
# 编排脚本的高层业务流程。
# 切换到 Mock 工具项目根目录。
change_to_project_root() {
  cd "$PROJECT_ROOT"
}
# 编排脚本的高层业务流程。
# 初始化脚本运行环境，并集中承载原有的顶层执行逻辑。
initialize_script_runtime() {
  setopt NO_NOMATCH
  set -euo pipefail
  : > "$LOG_FILE"
}
main() {
  show_script_intro_and_wait # 展示脚本说明并等待用户确认影响范围。
  initialize_script_runtime # 初始化 Shell 选项、日志、依赖和入口运行状态。
  change_to_project_root # 切换到 Mock 工具内层 Python 工程目录。
  check_environment # 检查当前步骤所需的环境、路径或输入条件。
  prepare_python_environment # 创建虚拟环境并安装 JobsMockTool 构建依赖。
  clean_build_outputs # 清理本次构建会覆盖的旧 build / dist 产物。
  build_macos_app # 使用 PyInstaller 生成 macOS App Bundle。
  build_dmg_installer # 把 App Bundle 封装成可拖拽安装的 DMG。
  show_build_result # 汇总输出安装包路径、Gatekeeper 提示和日志位置。
}

main "$@"
