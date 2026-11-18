from __future__ import annotations

from pathlib import Path

from ipa_reverse_tool.core.environment_doctor import run_doctor

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



def main() -> int:
    output_dir = Path.cwd() / "output" / "diagnostics"
    checks, json_path, md_path = run_doctor(output_dir)
    ok_count = sum(1 for item in checks if item.status == "ok")
    missing_count = len(checks) - ok_count
    jobs_prompt_print(f"环境体检完成：可用 {ok_count} 项，缺失 {missing_count} 项")
    jobs_prompt_print(f"JSON 报告：{json_path}")
    jobs_prompt_print(f"Markdown 报告：{md_path}")
    input(jobs_prompt_render("按回车退出...", question=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
