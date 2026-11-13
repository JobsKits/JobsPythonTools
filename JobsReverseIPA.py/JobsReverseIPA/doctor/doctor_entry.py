from __future__ import annotations

from pathlib import Path

from ipa_reverse_tool.core.environment_doctor import run_doctor

# JOBS_INPUT_CHOICE_STYLE_BEGIN
# 仅渲染终端提示选项；输入、默认值、EOF 和取消继续由原调用负责。
import os as _jobs_prompt_os
import re as _jobs_prompt_re
import sys as _jobs_prompt_sys


def jobs_prompt_render(text, stream=None):
    stream = _jobs_prompt_sys.stdout if stream is None else stream
    plain = _jobs_prompt_re.sub(r'\x1b\[[0-9;]*m', '', text)
    environment = _jobs_prompt_os.environ
    if ('NO_COLOR' in environment or not environment.get('TERM') or
            environment.get('TERM') == 'dumb' or environment.get('PLAIN_OUTPUT') == '1' or
            environment.get('IS_SOURCETREE_RUNTIME') == '1' or
            not _jobs_prompt_sys.stdin.isatty() or not stream.isatty()):
        return plain
    red = _jobs_prompt_re.compile(r'(?:输入)?(?:任意|任何)(?:非空)?(?:字符|内容|输入|键)|非空(?:字符|内容|输入)?|其它输入|其他输入|\bType (?:anything|any\S*)|\bPress any key', _jobs_prompt_re.I)
    green = _jobs_prompt_re.compile(r'(?:直接|仅|只需|只|按下|按)?\s*(?:回车|回車)|\b(?:Enter|Return)\b', _jobs_prompt_re.I)

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

    def segment(value, inherited=0):
        if not value:
            return value
        arbitrary, enter = red.search(value), eligible_green(value)
        if not inherited and arbitrary and enter and enter.start() < arbitrary.start():
            left, right = value[:arbitrary.start()], value[arbitrary.start():]
            connector = _jobs_prompt_re.search(r'(?:或者|或)\s*$', left)
            if connector:
                return segment(left[:connector.start()]) + connector.group() + segment(right, 31)
            return segment(left) + segment(right, 31)
        if not inherited and arbitrary and enter and arbitrary.start() < enter.start():
            connector = _jobs_prompt_re.search(r'或\s*(?:直接|仅|只需|只|按下|按)?(?:回车|回車)', value)
            if connector:
                return segment(value[:connector.start()], 31) + '或' + segment(value[connector.start() + 1:])
        match = arbitrary or enter
        kind = inherited or (31 if arbitrary else 32 if enter else 0)
        if not kind:
            return value
        start = 0 if inherited else match.start()
        return value[:start] + f'\x1b[1;{kind}m' + value[start:] + '\x1b[0m'

    output, inherited, depth = [], 0, 0
    parts = _jobs_prompt_re.split(r'([；;/|，,、？?：:=＝（）()\[\]【】\n])', plain)
    for index in range(0, len(parts), 2):
        part = parts[index]
        output.append(segment(part, inherited))
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
    return ''.join(output)


def jobs_prompt_print(*values, sep=' ', end='\n', file=None, flush=False):
    stream = _jobs_prompt_sys.stdout if file is None else file
    print(jobs_prompt_render(sep.join(str(value) for value in values), stream), end=end, file=stream, flush=flush)
# JOBS_INPUT_CHOICE_STYLE_END



def main() -> int:
    output_dir = Path.cwd() / "output" / "diagnostics"
    checks, json_path, md_path = run_doctor(output_dir)
    ok_count = sum(1 for item in checks if item.status == "ok")
    missing_count = len(checks) - ok_count
    print(f"环境体检完成：可用 {ok_count} 项，缺失 {missing_count} 项")
    print(f"JSON 报告：{json_path}")
    print(f"Markdown 报告：{md_path}")
    input(jobs_prompt_render("按回车退出..."))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
