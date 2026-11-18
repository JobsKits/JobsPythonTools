#requires -Version 5.1
<#
Jobs IPA 环境体检 Windows 构建辅助入口。
用途：检查 Python 与 PyInstaller，生成本机控制台 EXE。
影响：缺失依赖经确认安装；仅向本工具 dist 的独立时间目录写产物，不清理其它产物。
#>
[CmdletBinding()]
param(
    [string]$ProjectRoot = '',
    [switch]$Confirmed
)
$script:DoctorRoot = ''
$script:DoctorEntry = ''
$script:DoctorOutputDir = ''
$script:DoctorOutputFile = ''
$script:DoctorPython = ''
$script:DoctorLog = ''
# 按实际宿主能力判断是否允许终端样式。
function Test-JobsEnterChoiceColor {
    param([Collections.IDictionary]$Capabilities = $null)
    if ($null -eq $Capabilities) {
        try {
            $environment = [Environment]::GetEnvironmentVariables('Process')
            $Capabilities = @{ HostName = $Host.Name; InputRedirected = [Console]::IsInputRedirected; OutputRedirected = [Console]::IsOutputRedirected;
                               ErrorRedirected = [Console]::IsErrorRedirected; NoColorPresent = $environment.Contains('NO_COLOR');
                               PlainOutput = $env:PLAIN_OUTPUT; Term = $env:TERM; Windows = ([Environment]::OSVersion.Platform -eq [PlatformID]::Win32NT); VirtualTerminal = $false; SourceTree = ($env:IS_SOURCETREE_RUNTIME -eq '1') }
            if ($null -ne $Host.UI.PSObject.Properties['SupportsVirtualTerminal']) { $Capabilities.VirtualTerminal = $Host.UI.SupportsVirtualTerminal }
            foreach ($key in $environment.Keys) { if ([string]$key -match '^(?i:SOURCE_?TREE)') { $Capabilities.SourceTree = $true; break } }
        } catch { return $false }
    }
    return ($Capabilities.HostName -eq 'ConsoleHost' -and -not $Capabilities.InputRedirected -and -not $Capabilities.OutputRedirected -and
            -not $Capabilities.ErrorRedirected -and -not $Capabilities.NoColorPresent -and $Capabilities.PlainOutput -ne '1' -and
            $Capabilities.Term -ine 'dumb' -and (-not [string]::IsNullOrEmpty($Capabilities.Term) -or ($Capabilities.Contains('Windows') -and $Capabilities.Windows)) -and -not $Capabilities.SourceTree -and $Capabilities.VirtualTerminal)
}
# 判断当前宿主能否显示粗体。
function Test-JobsEnterChoiceBold {
    $property = $Host.UI.PSObject.Properties['SupportsVirtualTerminal']
    return ($null -ne $property -and [bool]$property.Value)
}
# 识别回车与非空输入选项的边界。
function Get-JobsEnterChoiceParts {
    param([string]$Text)
    $red = '(?:(?:\u8f93\u5165)?(?:\u4efb\u610f(?:\u975e\u7a7a)?(?:\u5b57\u7b26|\u5185\u5bb9|\u6587\u5b57|\u8f93\u5165)?|\u975e\u7a7a(?:\u8f93\u5165|\u5b57\u7b26|\u5185\u5bb9)?|(?:\u5176\u5b83|\u5176\u4ed6)(?:\u975e\u7a7a)?(?:\u8f93\u5165|\u5185\u5bb9|\u5b57\u7b26)?))|(?:any\s+(?:(?:other|non[- ]empty)\s+)?(?:input|text|characters?)|non[- ]empty\s+input)|(?:type\s+(?:anything|any\s+(?:characters?|text|input)))'
    $green = '(?:(?:\u76f4\u63a5|\u53ea\u9700|\u4ec5(?:\u9700)?|\u6309(?:\u4e0b)?|\u7a7a)?\s*\u56de\u8f66|(?:press\s+)?\bEnter\b(?!\s+(?:YES|REPAIR|CLEAN|CONTINUE)\b))'
    $pattern = '(?is)(?<red>(?:' + $red + ')[^;\uFF1B\r\n]*?(?=[;\uFF1B\r\n]|\z))|(?<green>(?:' + $green + ')[^;\uFF1B\r\n]*?(?=(?:' + $red + ')|[;\uFF1B\r\n]|\z))'
    $offset = 0
    foreach ($match in [regex]::Matches($Text, $pattern)) {
        if ($match.Index -gt $offset) { [pscustomobject]@{ Text = $Text.Substring($offset, $match.Index - $offset); Color = '' } }
        $prefix = [regex]::Split($Text.Substring(0, $match.Index), '[;\uFF1B\r\n]')[-1]
        $typed = $prefix -match '(?i)(?:\u8f93\u5165|\u952e\u5165|type|enter)\s*(?:\u5927\u5199\s*)?(?:YES|REPAIR|CLEAN|CONTINUE)\b|\u7cbe\u786e\u8f93\u5165|\u8f93\u5165[^;\uFF1B\r\n]*[\u540e\u518d]\s*$'
        $color = if ($match.Groups['red'].Success) { 'Red' } elseif ($typed) { '' } else { 'Green' }
        [pscustomobject]@{ Text = $match.Value; Color = $color }
        $offset = $match.Index + $match.Length
    }
    if ($offset -lt $Text.Length) { [pscustomobject]@{ Text = $Text.Substring($offset); Color = '' } }
}
# 识别需要突出显示的询问题干。
function Get-JobsQuestionChoiceParts {
    param([string]$Text)
    $plain = [regex]::Replace($Text, '\x1b\[[0-9;]*m', '')
    $questionBody = $true
    foreach ($part in @(Get-JobsEnterChoiceParts $plain)) {
        $isOption = $part.Color -eq 'Red' -or $part.Color -eq 'Green'
        foreach ($token in [regex]::Matches($part.Text, '[^；;/|，,、？?：:=＝（）()\[\]【】\r\n]+|[；;/|，,、？?：:=＝（）()\[\]【】\r\n]')) {
            $value = $token.Value
            $separator = $value -match '^[；;/|，,、？?：:=＝（）()\[\]【】\r\n]$'
            $color = ''
            if (-not $separator -and -not [string]::IsNullOrWhiteSpace($value)) {
                if ($isOption) { $color = $part.Color }
                elseif ($questionBody) { $color = 'Cyan' }
            }
            [pscustomobject]@{ Text = $value; Color = $color }
        }
        if ($isOption) { $questionBody = $false }
    }
}
# 展示副本的URL范围；不改写请求、参数或机器输出。
function Get-JobsUrlRanges {
    param([string]$Text)
    $pattern = '[A-Za-z][A-Za-z0-9+.-]*://[^\s<>"''\x1b]+'
    $punctuation = '，。；：！？、（）【】《》「」『』“”‘’'
    $offset = 0
    while ($offset -lt $Text.Length) {
        $match = [regex]::Match($Text.Substring($offset), $pattern)
        if (-not $match.Success) { break }
        $start = $offset + $match.Index
        $url = $match.Value
        foreach ($mark in $punctuation.ToCharArray()) {
            $at = $url.IndexOf($mark)
            if ($at -ge 0) { $url = $url.Substring(0, $at) }
        }
        while ($url.Length) {
            $last = $url.Substring($url.Length - 1, 1)
            $unmatched = $false
            foreach ($pair in @(@('(', ')'), @('[', ']'), @('{', '}'))) {
                if ($last -eq $pair[1] -and ([regex]::Matches($url, [regex]::Escape($pair[1]))).Count -gt ([regex]::Matches($url, [regex]::Escape($pair[0]))).Count) { $unmatched = $true }
            }
            if ('. , ; : ! ?'.Split(' ') -contains $last -or $unmatched) { $url = $url.Substring(0, $url.Length - 1) }
            else { break }
        }
        [pscustomobject]@{ Start = $start; End = $start + $url.Length }
        $offset = $start + $url.Length
    }
}
# 临时遮蔽URL，避免地址中的Enter或标点参与选项识别。
function Protect-JobsDisplayUrls {
    param([string]$Text)
    $builder = New-Object Text.StringBuilder
    $tokens = New-Object 'Collections.Generic.List[object]'
    $offset = 0; $number = 0
    foreach ($range in @(Get-JobsUrlRanges $Text)) {
        do { $number++; $token = [string][char]2 + 'U' + $number + [char]3 } while ($Text.Contains($token))
        [void]$builder.Append($Text.Substring($offset, $range.Start - $offset)).Append($token)
        $tokens.Add([pscustomobject]@{ Token = $token; Text = $Text.Substring($range.Start, $range.End - $range.Start) })
        $offset = $range.End
    }
    [void]$builder.Append($Text.Substring($offset))
    [pscustomobject]@{ Text = $builder.ToString(); Tokens = $tokens.ToArray() }
}
# 按可见字符映射原SGR；URL内部已有样式仍统一绿下划线，后文恢复原序列。
function Format-JobsUrlText {
    param([AllowEmptyString()][string]$Text, [switch]$Color)
    $control = '\x1b\][^\x1b\x07]*(?:\x07|\x1b\\)|\x1b\[[0-?]*[ -/]*[@-~]'
    $sgr = '\x1b\[[0-9;:]*m'
    $value = [regex]::Replace($Text, $control, {
        param($match)
        if ($Color -and $match.Value -match ('^' + $sgr + '$')) { return $match.Value }
        return ''
    })
    if (-not $Color) { return $value }
    $styles = @{}; $visible = New-Object Text.StringBuilder; $offset = 0
    foreach ($match in [regex]::Matches($value, $sgr)) {
        [void]$visible.Append($value.Substring($offset, $match.Index - $offset))
        $index = $visible.Length
        if (-not $styles.ContainsKey($index)) { $styles[$index] = '' }
        $styles[$index] += $match.Value
        $offset = $match.Index + $match.Length
    }
    [void]$visible.Append($value.Substring($offset))
    $plain = $visible.ToString(); $starts = @{}; $ends = @{}
    foreach ($range in @(Get-JobsUrlRanges $plain)) { $starts[$range.Start] = $true; $ends[$range.End - 1] = $true }
    $escape = [string][char]27; $active = ''; $inUrl = $false; $output = New-Object Text.StringBuilder
    for ($index = 0; $index -le $plain.Length; $index++) {
        if ($styles.ContainsKey($index)) {
            $tokens = $styles[$index]; [void]$output.Append($tokens)
            foreach ($match in [regex]::Matches($tokens, $sgr)) {
                $token = $match.Value; $code = $token.Substring(2, $token.Length - 3)
                $fields = $code.Split(';'); $reset = $code -eq ''
                for ($item = 0; $item -lt $fields.Count; $item++) {
                    if ($fields[$item] -eq '0') { $reset = $true }
                    if (@('38', '48', '58') -contains $fields[$item] -and $item + 1 -lt $fields.Count) {
                        if ($fields[$item + 1] -eq '2') { $item += 4 }
                        elseif ($fields[$item + 1] -eq '5') { $item += 2 }
                    }
                }
                if ($reset) { $active = '' }
                $active += $token
            }
            if ($inUrl) { [void]$output.Append($escape + '[32;4m') }
        }
        if ($index -eq $plain.Length) { break }
        if ($starts.ContainsKey($index)) { [void]$output.Append($escape + '[32;4m'); $inUrl = $true }
        [void]$output.Append($plain[$index])
        if ($ends.ContainsKey($index)) { [void]$output.Append($escape + '[0m' + $active); $inUrl = $false }
    }
    return $output.ToString()
}
# 使用现行询问分段，只在展示层合成样式；无颜色时返回纯文本。
function Format-JobsDisplayText {
    param([AllowEmptyString()][string]$Text, [switch]$Question, [switch]$Color, [string]$BaseStyle = '')
    if (-not $Color) { return (Format-JobsUrlText $Text) }
    $plain = Format-JobsUrlText $Text
    $protected = Protect-JobsDisplayUrls $plain
    $parts = if ($Question) { @(Get-JobsQuestionChoiceParts $protected.Text) } else { @(Get-JobsEnterChoiceParts $protected.Text) }
    $escape = [string][char]27
    if (-not $Question -and @($parts | Where-Object { $_.Color }).Count -eq 0) {
        $result = Format-JobsUrlText ($BaseStyle + $Text) -Color
    } else {
        $output = New-Object Text.StringBuilder
        foreach ($part in $parts) {
            $code = switch ($part.Color) { 'Red' { 31 } 'Green' { 32 } 'Cyan' { 36 } default { 0 } }
            if ($code) { [void]$output.Append($escape + '[1;' + $code + 'm' + $part.Text + $escape + '[0m' + $BaseStyle) }
            else { [void]$output.Append($BaseStyle + $part.Text) }
        }
        $formatted = $output.ToString()
        foreach ($item in $protected.Tokens) { $formatted = $formatted.Replace($item.Token, $item.Text) }
        $result = Format-JobsUrlText $formatted -Color
    }
    if ($BaseStyle) { $result += $escape + '[0m' }
    return $result
}
# 将调用者明确指定的ConsoleColor转为临时ANSI底色，函数结束后复位。
function Get-JobsDisplayBaseStyle {
    param([Collections.IDictionary]$Parameters)
    $codes = @{ Black=30; DarkBlue=34; DarkGreen=32; DarkCyan=36; DarkRed=31; DarkMagenta=35; DarkYellow=33; Gray=37; DarkGray=90; Blue=94; Green=92; Cyan=96; Red=91; Magenta=95; Yellow=93; White=97 }
    $style = ''; $escape = [string][char]27
    if ($Parameters.ContainsKey('ForegroundColor')) { $style += $escape + '[' + $codes[[string]$Parameters.ForegroundColor] + 'm' }
    if ($Parameters.ContainsKey('BackgroundColor')) { $style += $escape + '[' + ($codes[[string]$Parameters.BackgroundColor] + 10) + 'm' }
    return $style
}
# 显示询问、选项和地址，保留纯文本信息记录。
function Write-JobsEnterChoiceText {
    [CmdletBinding()]
    param([Parameter(Position=0)][AllowNull()][object]$Object, [switch]$NoNewline, [ConsoleColor]$ForegroundColor, [ConsoleColor]$BackgroundColor, [object]$Separator = ' ', [switch]$Question)
    $text = if ($Object -is [array]) { $Object -join [string]$Separator } else { [string]$Object }
    $plain = Format-JobsUrlText $text
    if (-not (Test-JobsEnterChoiceColor)) { Write-Host $plain -NoNewline:$NoNewline; return }
    $baseStyle = Get-JobsDisplayBaseStyle $PSBoundParameters
    $rendered = Format-JobsDisplayText $text -Question:$Question -Color -BaseStyle $baseStyle
    $message = New-Object Management.Automation.HostInformationMessage
    $message.Message = $plain
    $message.NoNewLine = [bool]$NoNewline
    if ($PSBoundParameters.ContainsKey('ForegroundColor')) { $message.ForegroundColor = $ForegroundColor }
    if ($PSBoundParameters.ContainsKey('BackgroundColor')) { $message.BackgroundColor = $BackgroundColor }
    Write-Information -MessageData $message -Tags 'JobsDisplay' -InformationAction SilentlyContinue
    [Console]::Write($rendered)
    if (-not $NoNewline) { [Console]::WriteLine() }
}
# 渲染提示后沿用原生输入读取协议。
function Read-JobsEnterChoiceHost {
    [CmdletBinding()]
    param([Parameter(Position=0)][string]$Prompt, [switch]$AsSecureString, [switch]$MaskInput)
    if (-not (Test-JobsEnterChoiceColor)) {
        $plainArguments = @{}
        foreach ($key in $PSBoundParameters.Keys) { $plainArguments[$key] = $PSBoundParameters[$key] }
        if ($plainArguments.ContainsKey('Prompt')) { $plainArguments.Prompt = Format-JobsUrlText $Prompt }
        return (Read-Host @plainArguments)
    }
    Write-JobsEnterChoiceText ($Prompt + ': ') -NoNewline -Question
    $readerArguments = @{}
    foreach ($key in $PSBoundParameters.Keys) {
        if ($key -ne 'Prompt') { $readerArguments[$key] = $PSBoundParameters[$key] }
    }
    return (Read-Host @readerArguments)
}

# 先展示固定用途；非交互调用必须明确传入父流程确认标志。
function Show-DoctorBuildIntro {
    Write-JobsEnterChoiceText 'Jobs IPA 环境体检 · Windows 本机构建'
    Write-JobsEnterChoiceText '用途：检查 Python 与 PyInstaller，生成 IPA环境体检.exe。'
    Write-JobsEnterChoiceText '影响：仅写当前工具 dist 的独立时间目录；不删除其它应用、源码或旧产物。'
    Write-JobsEnterChoiceText '缺失依赖会单独确认安装；日志位于系统临时目录，实际路径稍后显示。'
    Write-JobsEnterChoiceText '按回车继续；其它输入、EOF 或 Ctrl+C 取消。'
    if ($Confirmed) { return }
    if ([Console]::IsInputRedirected -or $Host.Name -ne 'ConsoleHost') {
        throw '需要可交互终端；父流程完成确认后可显式传入 -Confirmed。'
    }
    $answer = Read-JobsEnterChoiceHost '已了解用途和影响，按回车继续'
    if ($null -eq $answer -or $answer -ne '') { throw '已取消，尚未安装或构建。' }
}
# 确认后定位工程和输入，拒绝输出链接改向，再创建本轮私有日志。
function Initialize-DoctorBuildContext {
    $script:ErrorActionPreference = 'Stop'
    $candidate = $ProjectRoot
    if ([string]::IsNullOrWhiteSpace($candidate)) { $candidate = Join-Path $PSScriptRoot '..\..\..' }
    $item = Get-Item -LiteralPath $candidate -Force -ErrorAction Stop
    if (-not $item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
        throw 'ProjectRoot 必须是实际工程目录，不能是链接或普通文件。'
    }
    $script:DoctorRoot = $item.FullName
    $script:DoctorEntry = Join-Path $script:DoctorRoot 'doctor\doctor_entry.py\doctor_entry.py'
    if (-not (Test-Path -LiteralPath $script:DoctorEntry -PathType Leaf)) { throw ('缺少体检入口：' + $script:DoctorEntry) }
    $dist = Join-Path (Split-Path -Parent $script:DoctorRoot) 'dist'
    if (Test-Path -LiteralPath $dist) {
        $distItem = Get-Item -LiteralPath $dist -Force
        if (-not $distItem.PSIsContainer -or ($distItem.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
            throw ('拒绝非目录或链接输出位置：' + $dist)
        }
    }
    $stamp = Get-Date -Format 'yyyy.MM.dd HH-mm-ss'
    $script:DoctorOutputDir = Join-Path $dist $stamp
    if (Test-Path -LiteralPath $script:DoctorOutputDir) { throw ('本轮产物目录已存在，保留原目录：' + $script:DoctorOutputDir) }
    $script:DoctorOutputFile = Join-Path $script:DoctorOutputDir 'IPA环境体检.exe'
    $script:DoctorLog = Join-Path ([IO.Path]::GetTempPath()) ('JobsDoctorBuild-' + [Guid]::NewGuid().ToString('N') + '.log')
    [IO.File]::WriteAllText($script:DoctorLog, '', (New-Object Text.UTF8Encoding($false)))
    Write-DoctorBuildMessage ('日志：' + $script:DoctorLog)
}
# 显示与落盘保持纯文本，避免控制码写入诊断日志。
function Write-DoctorBuildMessage {
    param([string]$Message)
    $plain = [regex]::Replace($Message, ([char]27 + '\[[0-9;]*m'), '')
    Write-JobsEnterChoiceText $plain
    if ($script:DoctorLog) { [IO.File]::AppendAllText($script:DoctorLog, $plain + [Environment]::NewLine, (New-Object Text.UTF8Encoding($false))) }
}
# 原生命令使用参数数组，先保存退出码再输出诊断，失败阻止后续步骤。
function Invoke-DoctorPython {
    param([string[]]$Arguments)
    $lines = & $script:DoctorPython -B @Arguments 2>&1
    $result = $LASTEXITCODE
    foreach ($line in $lines) { Write-DoctorBuildMessage ([string]$line) }
    if ($result -ne 0) { throw ('Python 命令失败，退出码：' + $result) }
}
# 检查真实解释器，不因 PATH 中存在 shim 就视为可用。
function Test-DoctorPython {
    $command = Get-Command python -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($null -eq $command) { throw '未找到可用 Python；请使用上级本机打包入口准备运行时。' }
    $script:DoctorPython = $command.Source
    Invoke-DoctorPython -Arguments @('-c', 'import sys; print(sys.version)')
}
# 健康 PyInstaller 直接复用；仅缺失时确认并准备，不主动升级 pip。
function Ensure-DoctorBuildDependencies {
    & $script:DoctorPython -B -m PyInstaller --version > $null 2>&1
    if ($LASTEXITCODE -eq 0) { Write-DoctorBuildMessage '复用健康 PyInstaller，不安装或升级依赖。'; return }
    if ([Console]::IsInputRedirected -or $Host.Name -ne 'ConsoleHost') { throw '缺失 PyInstaller，需要在交互终端确认安装；未执行安装。' }
    $answer = Read-JobsEnterChoiceHost '缺失必需 PyInstaller，直接回车安装；任意非空输入取消'
    if ($null -eq $answer -or $answer -ne '') { throw '已取消，未开始打包。' }
    & $script:DoctorPython -B -m pip --version > $null 2>&1
    if ($LASTEXITCODE -ne 0) { Invoke-DoctorPython -Arguments @('-m', 'ensurepip') }
    Invoke-DoctorPython -Arguments @('-m', 'pip', 'install', 'pyinstaller')
    Invoke-DoctorPython -Arguments @('-m', 'PyInstaller', '--version')
}
# 从工程实际位置执行构建，结束时恢复父调用方工作目录。
function Invoke-DoctorBuild {
    Push-Location -LiteralPath $script:DoctorRoot
    try {
        Invoke-DoctorPython -Arguments @('-m', 'PyInstaller', '--distpath', $script:DoctorOutputDir,
            '--onefile', '--console', '--name', 'IPA环境体检', '--paths', $script:DoctorRoot, $script:DoctorEntry)
    } finally {
        Pop-Location
    }
}
# 只确认当前时间目录的真实非空 EXE，不以旧包冒充本次成功。
function Complete-DoctorBuild {
    if (-not (Test-Path -LiteralPath $script:DoctorOutputFile -PathType Leaf) -or
        (Get-Item -LiteralPath $script:DoctorOutputFile).Length -eq 0) {
        throw ('未生成有效构建产物：' + $script:DoctorOutputFile)
    }
    Write-DoctorBuildMessage ('构建完成：' + $script:DoctorOutputFile)
}
# 高层入口仅编排职责函数；取消、异常和失败统一由边界传递。
function Main {
    Show-DoctorBuildIntro # 先展示用途与影响，再决定是否继续。
    Initialize-DoctorBuildContext # 确认后解析输入、输出并建立本轮日志。
    Test-DoctorPython # 复检真实 Python 解释器。
    Ensure-DoctorBuildDependencies # 仅按需准备缺失依赖并复检。
    Invoke-DoctorBuild # 本机生成体检 EXE 并恢复调用工作目录。
    Complete-DoctorBuild # 核验本轮真实产物后报告结果。
}
try {
    Main
    exit 0
} catch {
    [Console]::Error.WriteLine($_.Exception.Message)
    if ($script:DoctorLog) { [Console]::Error.WriteLine('日志：' + $script:DoctorLog) }
    exit 1
}
