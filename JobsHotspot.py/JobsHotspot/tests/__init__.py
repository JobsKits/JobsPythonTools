"""Jobs：让 unittest 发现同名目录中的真实测试，不把零测试当作成功。"""
import fnmatch
import importlib.util
from pathlib import Path
import sys
import unittest

# 逐包加载测试，保持同级夹具导入；入口命令需使用 -s tests -t .。
def load_tests(loader, standard_tests, pattern):
    tests_root = Path(__file__).resolve().parent
    project_root = tests_root.parent
    pattern = pattern or 'test*.py'
    packaged = sorted(path for path in tests_root.glob('*/*.py')
                      if path.parent.name == path.name and fnmatch.fnmatch(path.name, pattern))
    if not packaged:
        raise RuntimeError('未发现匹配的同名包装测试：' + pattern)
    for directory in [project_root, project_root / 'src', *(path.parent for path in tests_root.glob('*/*.py'))]:
        if directory.is_dir() and str(directory) not in sys.path:
            sys.path.insert(0, str(directory))
    suite = unittest.TestSuite()
    for path in packaged:
        name = path.stem
        module = sys.modules.get(name)
        if module is None or Path(getattr(module, '__file__', '')).resolve() != path:
            spec = importlib.util.spec_from_file_location(name, path)
            if spec is None or spec.loader is None:
                raise RuntimeError('不能加载测试：' + str(path))
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
        suite.addTests(loader.loadTestsFromModule(module))
    if suite.countTestCases() == 0:
        raise RuntimeError('匹配的测试没有可执行用例：' + pattern)
    return suite
