#!/bin/zsh
# 脚本自述：转交 Mock 工具构建入口；内层展示说明并确认后生成 APP / DMG。
# shell: zsh
# 转交现有打包器，让用户从第一层直接开始构建。
run_builder() {
  # zsh 函数内的 $0 会变成函数名，%x 保留定义函数的脚本路径。
  local script_dir="${${(%):-%x}:A:h}"
  "${script_dir}/build_macos.command/build_macos.command" "$@"
}
# 编排唯一打包入口。
main() {
  run_builder "$@" # 内层负责确认、构建及最新产物快捷方式。
}
main "$@"
