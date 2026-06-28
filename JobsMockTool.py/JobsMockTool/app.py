"""
JobsMockTool
本地 Mock API 图形化工具。

本版本使用 PySide6 构建桌面界面，并在顶部集成 QWebEngineView，
直接加载 https://dragonir.github.io/3d/#/earth 作为可拖拽 3D 地球展示区。
"""
from __future__ import annotations

import copy
import json
import threading
from datetime import datetime
import traceback
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Optional, Tuple

from PySide6.QtCore import QObject, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QAction, QCloseEvent, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QStackedWidget,
    QStyle,
    QSystemTrayIcon,
    QTabWidget,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
except Exception:  # pragma: no cover - 允许缺少 WebEngine 时降级显示
    QWebEngineView = None  # type: ignore[assignment]

APP_NAME = "JobsMockTool"
APP_VERSION = "5.0"
EARTH_URL = "https://dragonir.github.io/3d/#/earth"
HTTP_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"]
SERVER_MODES = {
    "shared_port": "模式一：同一服务端口，按路径区分接口",
    "per_endpoint_port": "模式二：每个接口独立端口",
}
NODE_TYPES = [
    "dict",
    "list",
    "string",
    "number",
    "boolean",
    "null",
    "object_json_string",
]
CONTAINER_TYPES = {"dict", "list"}
DEFAULT_RESPONSE_HEADERS = {
    "Content-Type": "application/json; charset=utf-8",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET,POST,PUT,PATCH,DELETE,OPTIONS,HEAD",
    "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With",
}
DEFAULT_REQUEST_HEADERS = {
    "Content-Type": "application/json; charset=utf-8",
    "Accept": "application/json",
}
TYPE_LABELS = {
    "dict": "字典 / JSON Object，可继续添加子节点",
    "list": "数组 / JSON Array，可继续添加子节点",
    "string": "字符串",
    "number": "数字",
    "boolean": "布尔值 true/false",
    "null": "空值 null",
    "object_json_string": "对象 JSON 字符串，需要调用方二次解码",
}
WEEKDAYS_ZH = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]


def format_location_text(info: Dict[str, Any]) -> str:
    # 只展示人类可读的省市区，不展示经纬度。
    candidates = []
    for key in ("regionName", "region", "province", "city", "country_name", "country"):
        value = str(info.get(key, "")).strip()
        if value and value not in candidates:
            candidates.append(value)
    city = str(info.get("city", "")).strip()
    region = str(info.get("regionName", info.get("region", info.get("province", "")))).strip()
    country = str(info.get("country_name", info.get("country", ""))).strip()
    if region and city:
        return f"{region}{city if city not in region else ''}"
    if city:
        return city
    if region:
        return region
    if country:
        return country
    return "未能自动识别"


class LocationSignalBridge(QObject):
    location_ready = Signal(str)


@dataclass
class DataNode:
    node_id: str
    key: str
    node_type: str
    value: str = ""
    children: List["DataNode"] = field(default_factory=list)

    def is_container(self) -> bool:
        return self.node_type in CONTAINER_TYPES


@dataclass
class ResponseCase:
    case_id: str
    name: str
    status_code: int
    match_text: str
    root_node: DataNode


@dataclass
class EndpointConfig:
    endpoint_id: str
    name: str
    method: str
    path: str
    port: str
    headers_text: str
    params_text: str
    cases: List[ResponseCase] = field(default_factory=list)


def uid() -> str:
    return str(uuid.uuid4())


def new_node(key: str, node_type: str, value: str = "") -> DataNode:
    return DataNode(node_id=uid(), key=key, node_type=node_type, value=value)


def default_tree() -> DataNode:
    root = new_node("root", "dict")
    root.children.extend(
        [
            new_node("code", "number", "200"),
            new_node("message", "string", "success"),
            new_node("success", "boolean", "true"),
        ]
    )
    data = new_node("data", "dict")
    items = new_node("items", "list")
    first = new_node("", "dict")
    first.children.extend(
        [
            new_node("id", "number", "1"),
            new_node("name", "string", "示例数据"),
            new_node("extra", "object_json_string", '{"source":"mock","needDecode":true}'),
        ]
    )
    items.children.append(first)
    data.children.append(items)
    root.children.append(data)
    return root


def empty_success_tree() -> DataNode:
    root = new_node("root", "dict")
    root.children.extend(
        [
            new_node("code", "number", "200"),
            new_node("message", "string", "ok"),
            new_node("data", "dict"),
        ]
    )
    return root


def python_to_node(value: Any, key: str = "root") -> DataNode:
    if isinstance(value, dict):
        node = new_node(key, "dict")
        for child_key, child_value in value.items():
            node.children.append(python_to_node(child_value, str(child_key)))
        return node
    if isinstance(value, list):
        node = new_node(key, "list")
        for item in value:
            node.children.append(python_to_node(item, ""))
        return node
    if isinstance(value, bool):
        return new_node(key, "boolean", "true" if value else "false")
    if value is None:
        return new_node(key, "null", "")
    if isinstance(value, (int, float)):
        return new_node(key, "number", str(value))
    if isinstance(value, str):
        return new_node(key, "string", value)
    return new_node(key, "object_json_string", json.dumps(value, ensure_ascii=False))


def clone_node(node: DataNode) -> DataNode:
    cloned = new_node(node.key, node.node_type, node.value)
    cloned.children = [clone_node(child) for child in node.children]
    return cloned


def node_to_dict(node: DataNode) -> Dict[str, Any]:
    return {
        "key": node.key,
        "node_type": node.node_type,
        "value": node.value,
        "children": [node_to_dict(child) for child in node.children],
    }


def node_from_dict(data: Dict[str, Any]) -> DataNode:
    node = new_node(
        str(data.get("key", "")),
        str(data.get("node_type", "string")),
        str(data.get("value", "")),
    )
    node.children = [node_from_dict(child) for child in data.get("children", [])]
    return node


def parse_json_text(text: str, default: Optional[Any] = None) -> Any:
    raw = text.strip()
    if not raw:
        return default
    return json.loads(raw)


def parse_number(value: str) -> Any:
    raw = str(value).strip()
    if raw == "":
        return 0
    if any(ch in raw.lower() for ch in [".", "e"]):
        return float(raw)
    return int(raw)


def parse_bool(value: str) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y", "on", "是"}


def node_to_python(node: DataNode) -> Any:
    if node.node_type == "dict":
        result: Dict[str, Any] = {}
        for child in node.children:
            key = child.key.strip() or "field"
            result[key] = node_to_python(child)
        return result
    if node.node_type == "list":
        return [node_to_python(child) for child in node.children]
    if node.node_type == "string":
        return node.value
    if node.node_type == "number":
        return parse_number(node.value)
    if node.node_type == "boolean":
        return parse_bool(node.value)
    if node.node_type == "null":
        return None
    if node.node_type == "object_json_string":
        raw = node.value.strip()
        if not raw:
            return "{}"
        return raw
    return node.value


def normalize_path(path: str) -> str:
    path = path.strip() or "/api/mock"
    if not path.startswith("/"):
        path = "/" + path
    return path


def pretty_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def shorten(text: str, max_len: int = 54) -> str:
    text = text.replace("\n", " ").strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def format_node_label(node: DataNode, is_root: bool = False, index: Optional[int] = None) -> str:
    if is_root:
        prefix = "root"
    elif node.key:
        prefix = node.key
    elif index is not None:
        prefix = f"[{index}]"
    else:
        prefix = "[item]"

    if node.node_type == "dict":
        return f"{prefix}  {{}}"
    if node.node_type == "list":
        return f"{prefix}  []"
    if node.node_type == "string":
        return f'{prefix}: "{shorten(node.value, 48)}"'
    if node.node_type == "number":
        return f"{prefix}: {node.value or 0}"
    if node.node_type == "boolean":
        raw = node.value.strip().lower() if node.value.strip() else "false"
        return f"{prefix}: {raw}"
    if node.node_type == "null":
        return f"{prefix}: null"
    if node.node_type == "object_json_string":
        return f"{prefix}: JSON字符串({shorten(node.value, 36) or '{}'})"
    return f"{prefix}: {shorten(node.value, 48)}"


def case_to_dict(case: ResponseCase) -> Dict[str, Any]:
    return {
        "name": case.name,
        "status_code": case.status_code,
        "match_text": case.match_text,
        "root_node": node_to_dict(case.root_node),
    }


def case_from_dict(data: Dict[str, Any]) -> ResponseCase:
    return ResponseCase(
        case_id=uid(),
        name=str(data.get("name", "默认响应")),
        status_code=int(data.get("status_code", 200)),
        match_text=str(data.get("match_text", "{}")),
        root_node=node_from_dict(data.get("root_node", node_to_dict(default_tree()))),
    )


def endpoint_to_dict(endpoint: EndpointConfig) -> Dict[str, Any]:
    return {
        "name": endpoint.name,
        "method": endpoint.method,
        "path": endpoint.path,
        "port": endpoint.port,
        "headers_text": endpoint.headers_text,
        "params_text": endpoint.params_text,
        "cases": [case_to_dict(case) for case in endpoint.cases],
    }


def endpoint_from_dict(data: Dict[str, Any]) -> EndpointConfig:
    cases = [case_from_dict(item) for item in data.get("cases", [])]
    if not cases:
        cases = [new_response_case("默认响应", default_tree())]
    return EndpointConfig(
        endpoint_id=uid(),
        name=str(data.get("name", "接口")),
        method=str(data.get("method", "GET")).upper(),
        path=normalize_path(str(data.get("path", "/api/mock"))),
        port=str(data.get("port", "8765")),
        headers_text=str(data.get("headers_text", pretty_json(DEFAULT_RESPONSE_HEADERS))),
        params_text=str(data.get("params_text", pretty_json({"page": 1, "pageSize": 10}))),
        cases=cases,
    )


def new_response_case(name: str = "默认响应", root_node: Optional[DataNode] = None) -> ResponseCase:
    return ResponseCase(
        case_id=uid(),
        name=name,
        status_code=200,
        match_text="{}",
        root_node=root_node or default_tree(),
    )


def new_endpoint(index: int = 1) -> EndpointConfig:
    return EndpointConfig(
        endpoint_id=uid(),
        name=f"接口 {index}",
        method="GET",
        path=f"/api/mock{'' if index == 1 else index}",
        port=str(8765 + index - 1),
        headers_text=pretty_json(DEFAULT_RESPONSE_HEADERS),
        params_text=pretty_json({"page": 1, "pageSize": 10}),
        cases=[new_response_case("默认响应", default_tree())],
    )


def parse_port(raw: str) -> int:
    try:
        port = int(str(raw).strip())
    except Exception as exc:
        raise ValueError("端口必须是数字") from exc
    if not (1 <= port <= 65535):
        raise ValueError("端口范围必须是 1-65535")
    return port


def parse_status_code(raw: Any) -> int:
    try:
        code = int(str(raw).strip())
    except Exception as exc:
        raise ValueError("状态码必须是数字") from exc
    if not (100 <= code <= 599):
        raise ValueError("HTTP 状态码范围必须是 100-599")
    return code


def smart_parse_body(body_text: str, content_type: str = "") -> Any:
    raw = body_text.strip()
    if not raw:
        return {}
    if "json" in content_type.lower():
        try:
            return json.loads(raw)
        except Exception:
            return raw
    try:
        return json.loads(raw)
    except Exception:
        parsed_qs = urllib.parse.parse_qs(raw, keep_blank_values=True)
        if parsed_qs:
            return {k: v[0] if len(v) == 1 else v for k, v in parsed_qs.items()}
        return raw


def single_or_list_dict(pairs: List[Tuple[str, str]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            if not isinstance(result[key], list):
                result[key] = [result[key]]
            result[key].append(value)
        else:
            result[key] = value
    return result


def flatten_merge(query: Dict[str, Any], body: Any) -> Dict[str, Any]:
    merged = dict(query)
    if isinstance(body, dict):
        merged.update(body)
    return merged


def nested_get(data: Any, path: str) -> Any:
    current = data
    if path == "":
        return current
    for part in path.split("."):
        if isinstance(current, dict):
            if part in current:
                current = current[part]
            else:
                lowered = {str(k).lower(): v for k, v in current.items()}
                if part.lower() in lowered:
                    current = lowered[part.lower()]
                else:
                    return None
        elif isinstance(current, list):
            try:
                current = current[int(part)]
            except Exception:
                return None
        else:
            return None
    return current


def value_equals(actual: Any, expected: Any) -> bool:
    if isinstance(actual, list):
        return any(value_equals(item, expected) for item in actual)
    if isinstance(expected, bool):
        if isinstance(actual, bool):
            return actual == expected
        return parse_bool(str(actual)) == expected
    if isinstance(expected, (int, float)) and not isinstance(expected, bool):
        try:
            return float(actual) == float(expected)
        except Exception:
            return False
    if expected is None:
        return actual is None or str(actual).lower() == "null"
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return False
        for key, expected_value in expected.items():
            if not value_equals(nested_get(actual, str(key)), expected_value):
                return False
        return True
    return str(actual) == str(expected)


def get_match_value(context: Dict[str, Any], key: str) -> Any:
    if "." in key:
        scope, rest = key.split(".", 1)
        if scope in context:
            return nested_get(context[scope], rest)
    for scope in ("params", "body", "query", "headers"):
        value = nested_get(context.get(scope, {}), key)
        if value is not None:
            return value
    return None


def match_condition(condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
    if not condition:
        return True
    for key, expected in condition.items():
        actual = get_match_value(context, str(key))
        if not value_equals(actual, expected):
            return False
    return True


class MockRequestHandler(BaseHTTPRequestHandler):
    server_version = f"{APP_NAME}/{APP_VERSION}"

    def log_message(self, format: str, *args: Any) -> None:
        return

    def do_OPTIONS(self) -> None:  # noqa: N802
        self._handle_request(send_body=False, preflight=True)

    def do_HEAD(self) -> None:  # noqa: N802
        self._handle_request(send_body=False)

    def do_GET(self) -> None:  # noqa: N802
        self._handle_request()

    def do_POST(self) -> None:  # noqa: N802
        self._handle_request()

    def do_PUT(self) -> None:  # noqa: N802
        self._handle_request()

    def do_PATCH(self) -> None:  # noqa: N802
        self._handle_request()

    def do_DELETE(self) -> None:  # noqa: N802
        self._handle_request()

    def _read_request_body(self) -> str:
        length = int(self.headers.get("Content-Length", "0") or 0)
        if length <= 0:
            return ""
        return self.rfile.read(length).decode("utf-8", errors="replace")

    def _build_context(self, parsed_url: urllib.parse.ParseResult) -> Dict[str, Any]:
        query = single_or_list_dict(urllib.parse.parse_qsl(parsed_url.query, keep_blank_values=True))
        raw_body = self._read_request_body()
        headers = {str(k): str(v) for k, v in self.headers.items()}
        body = smart_parse_body(raw_body, self.headers.get("Content-Type", ""))
        return {
            "query": query,
            "body": body,
            "params": flatten_merge(query, body),
            "headers": headers,
        }

    def _pick_case(self, runtime: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        cases: List[Dict[str, Any]] = runtime["cases"]
        default_case = cases[0]
        for item in cases:
            if not item["match"]:
                default_case = item
                continue
            if match_condition(item["match"], context):
                return item
        return default_case

    def _handle_request(self, send_body: bool = True, preflight: bool = False) -> None:
        route_map: Dict[Tuple[str, str], Dict[str, Any]] = getattr(self.server, "route_map", {})
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        method = self.command.upper()

        if preflight:
            runtime = next(iter(route_map.values()), None)
            headers = runtime["headers"] if runtime else DEFAULT_RESPONSE_HEADERS
            self.send_response(204)
            for key, value in headers.items():
                if key.lower() != "content-length":
                    self.send_header(key, str(value))
            self.end_headers()
            return

        key = (method, path)
        runtime = route_map.get(key)
        if not runtime and method == "HEAD":
            runtime = route_map.get(("GET", path))

        if not runtime:
            methods_for_path = sorted({m for (m, p) in route_map.keys() if p == path})
            if methods_for_path:
                self._write_json(
                    405,
                    {
                        "error": "METHOD_NOT_ALLOWED",
                        "message": "该路径存在，但请求方式不匹配",
                        "available_methods": methods_for_path,
                        "requested_method": method,
                        "requested_path": path,
                    },
                    DEFAULT_RESPONSE_HEADERS,
                    send_body,
                )
                return

            available = [
                {"method": m, "path": p}
                for (m, p) in sorted(route_map.keys(), key=lambda item: (item[1], item[0]))
            ]
            self._write_json(
                404,
                {
                    "error": "NOT_FOUND",
                    "message": "当前本地服务没有配置这个接口",
                    "requested_method": method,
                    "requested_path": path,
                    "available_routes": available,
                },
                DEFAULT_RESPONSE_HEADERS,
                send_body,
            )
            return

        context = self._build_context(parsed)
        picked_case = self._pick_case(runtime, context)
        self._write_json(
            picked_case["status_code"],
            picked_case["response_data"],
            runtime["headers"],
            send_body,
        )

    def _write_json(self, status: int, data: Any, headers: Dict[str, str], send_body: bool = True) -> None:
        payload = pretty_json(data).encode("utf-8")
        self.send_response(status)
        sent_content_type = False
        for key, value in headers.items():
            if key.lower() == "content-length":
                continue
            if key.lower() == "content-type":
                sent_content_type = True
            self.send_header(key, str(value))
        if not sent_content_type:
            self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        if send_body:
            self.wfile.write(payload)


class NodeDialog(QDialog):
    def __init__(
        self,
        parent: QWidget,
        title: str,
        parent_type: str,
        key: str = "",
        node_type: str = "string",
        value: str = "",
        allow_key_edit: bool = True,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.result_data: Optional[Dict[str, str]] = None
        self.parent_type = parent_type
        self.allow_key_edit = allow_key_edit

        layout = QVBoxLayout(self)
        form = QFormLayout()
        layout.addLayout(form)

        self.key_edit = QLineEdit(key)
        if parent_type == "list":
            self.key_edit.setText(key or "数组项自动按顺序生成")
            self.key_edit.setEnabled(False)
        elif not allow_key_edit:
            self.key_edit.setEnabled(False)
        form.addRow("字段名 / 数组项说明", self.key_edit)

        self.type_combo = QComboBox()
        self.type_combo.addItems(NODE_TYPES)
        self.type_combo.setCurrentText(node_type)
        self.type_combo.currentTextChanged.connect(self._refresh_hint)
        form.addRow("数据类型", self.type_combo)

        self.hint_label = QLabel("")
        self.hint_label.setObjectName("mutedLabel")
        form.addRow("", self.hint_label)

        self.value_text = QTextEdit()
        self.value_text.setMinimumHeight(150)
        self.value_text.setPlainText(value)
        form.addRow("字段值（容器类型可留空）", self.value_text)

        btns = QHBoxLayout()
        btns.addStretch(1)
        cancel_btn = QPushButton("取消")
        ok_btn = QPushButton("确定")
        ok_btn.setObjectName("primaryButton")
        cancel_btn.clicked.connect(self.reject)
        ok_btn.clicked.connect(self._confirm)
        btns.addWidget(ok_btn)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns)
        self.resize(540, 360)
        self._refresh_hint()

    def _refresh_hint(self) -> None:
        node_type = self.type_combo.currentText()
        self.hint_label.setText(TYPE_LABELS.get(node_type, ""))
        if node_type in CONTAINER_TYPES:
            self.value_text.setStyleSheet("background:#f8fafc;color:#111111;")
        else:
            self.value_text.setStyleSheet("background:#ffffff;color:#111111;")

    def _confirm(self) -> None:
        node_type = self.type_combo.currentText()
        key = self.key_edit.text().strip()
        value = self.value_text.toPlainText().strip()
        if self.parent_type == "dict" and self.allow_key_edit and not key:
            QMessageBox.warning(self, "字段名必填", "父节点是字典时，子节点必须填写字段名。")
            return
        if node_type == "number" and value:
            try:
                parse_number(value)
            except Exception:
                QMessageBox.warning(self, "数字格式不正确", "数字类型请填写整数或小数。")
                return
        if node_type == "boolean" and value and value.strip().lower() not in {
            "true", "false", "1", "0", "yes", "no", "y", "n", "on", "off", "是", "否"
        }:
            QMessageBox.warning(self, "布尔值格式不正确", "布尔值建议填写 true / false。")
            return
        if node_type == "object_json_string" and value:
            try:
                json.loads(value)
            except Exception:
                ok = QMessageBox.question(
                    self,
                    "对象字符串不是合法 JSON",
                    "该值会按字符串返回，但目前看起来不是合法 JSON。仍然保存吗？",
                )
                if ok != QMessageBox.StandardButton.Yes:
                    return
        self.result_data = {"key": key, "node_type": node_type, "value": value}
        self.accept()


class JobsMockTool(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1600, 960)
        # 最小窗口尺寸要兜住完整功能区：低于这个尺寸时不允许继续压缩，避免控件被外框裁切。
        self.setMinimumSize(1600, 960)

        self.endpoints: List[EndpointConfig] = [new_endpoint(1)]
        self.current_endpoint_id: Optional[str] = None
        self.current_case_id: Optional[str] = None
        self.root_node: DataNode = self.endpoints[0].cases[0].root_node
        self.node_map: Dict[str, DataNode] = {}
        self.servers: Dict[int, ThreadingHTTPServer] = {}
        self.server_threads: Dict[int, threading.Thread] = {}
        self._loading = False
        self.location_text = "自动识别中..."
        self.location_bridge = LocationSignalBridge()
        self.location_bridge.location_ready.connect(self._on_location_ready)

        self._build_ui()
        self._setup_system_tray()
        self._refresh_endpoint_list(select_id=self.endpoints[0].endpoint_id)
        self._start_header_clock()
        self._detect_location_async()

    def _setup_system_tray(self) -> None:
        self.tray_icon: Optional[QSystemTrayIcon] = None
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return

        icon = QIcon("icon.png")
        if icon.isNull():
            icon = self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        self.setWindowIcon(icon)

        tray_menu = QMenu(self)
        show_action = QAction("显示 JobsMockTool", tray_menu)
        quit_action = QAction("退出 JobsMockTool", tray_menu)
        show_action.triggered.connect(self._restore_from_system_tray)
        quit_action.triggered.connect(self._quit_from_system_tray)
        tray_menu.addAction(show_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)

        self.tray_icon = QSystemTrayIcon(icon, self)
        self.tray_icon.setToolTip(APP_NAME)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_system_tray_activated)
        self.tray_icon.show()

    def _restore_from_system_tray(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _on_system_tray_activated(
        self,
        reason: QSystemTrayIcon.ActivationReason,
    ) -> None:
        if reason in {
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        }:
            self._restore_from_system_tray()

    def _quit_from_system_tray(self) -> None:
        self._stop_servers()
        QApplication.quit()

    def _start_header_clock(self) -> None:
        self.header_timer = QTimer(self)
        self.header_timer.timeout.connect(self._refresh_header_meta)
        self.header_timer.start(1000)
        self._refresh_header_meta()

    def _refresh_header_meta(self) -> None:
        now = datetime.now()
        week = WEEKDAYS_ZH[now.weekday()]
        text = f"⏰ {now:%Y年%m月%d日 %H:%M:%S}｜{week}｜📌 {self.location_text}"
        if hasattr(self, "meta_label"):
            self.meta_label.setText(text)

    def _detect_location_async(self) -> None:
        def worker() -> None:
            location = "未能自动识别"
            apis = [
                "http://ip-api.com/json/?lang=zh-CN",
                "https://ipapi.co/json/",
            ]
            for url in apis:
                try:
                    req = urllib.request.Request(url, headers={"User-Agent": f"{APP_NAME}/desktop"})
                    with urllib.request.urlopen(req, timeout=4) as resp:
                        payload = resp.read().decode("utf-8", errors="replace")
                    info = json.loads(payload)
                    candidate = format_location_text(info)
                    if candidate and candidate != "未能自动识别":
                        location = candidate
                        break
                except Exception:
                    continue
            self.location_bridge.location_ready.emit(location)

        threading.Thread(target=worker, daemon=True).start()

    def _on_location_ready(self, location: str) -> None:
        self.location_text = location
        self._refresh_header_meta()

    def _build_ui(self) -> None:
        self.setStyleSheet(STYLE_SHEET)
        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(14, 10, 14, 14)
        outer.setSpacing(10)
        outer.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)

        header = QFrame()
        header.setObjectName("headerFrame")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(2, 2, 2, 2)
        header_layout.setSpacing(18)
        outer.addWidget(header)

        left_header = QVBoxLayout()
        title = QLabel(APP_NAME)
        title.setObjectName("titleLabel")
        subtitle = QLabel("本地 Mock 接口配置 + 多接口服务模式 + 条件响应 + 内置接口请求测试")
        subtitle.setObjectName("subtitleLabel")
        self.meta_label = QLabel("⏰ --｜星期--｜📌 自动识别中...")
        self.meta_label.setObjectName("metaLabel")
        self.status_label = QLabel("未启动服务")
        self.status_label.setObjectName("statusLabel")
        left_header.addWidget(title)
        left_header.addWidget(subtitle)
        left_header.addWidget(self.meta_label)
        left_header.addWidget(self.status_label)
        left_header.addStretch(1)
        header_layout.addLayout(left_header, 0)
        header_layout.addStretch(1)

        self.earth_panel = self._make_earth_panel()
        header_layout.addWidget(self.earth_panel, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # 自定义选项卡栏：强制左对齐，避免系统样式把 QTabWidget 的 Tab 居中。
        tab_bar = QFrame()
        tab_bar.setObjectName("customTabBar")
        tab_layout = QHBoxLayout(tab_bar)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.setSpacing(0)
        self.config_tab_button = QPushButton("配置请求的数据")
        self.request_tab_button = QPushButton("请求配置的数据")
        for btn in (self.config_tab_button, self.request_tab_button):
            btn.setObjectName("tabButton")
            btn.setCheckable(True)
            btn.setMinimumWidth(160)
            btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            tab_layout.addWidget(btn)
        tab_layout.addStretch(1)
        outer.addWidget(tab_bar, 0)

        # 主内容区域增加明确边框，形成和外层窗口分离的配置工作区。
        self.content_frame = QFrame()
        self.content_frame.setObjectName("contentFrame")
        self.content_frame.setMinimumHeight(690)
        self.content_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        content_layout = QVBoxLayout(self.content_frame)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(0)
        content_layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        outer.addWidget(self.content_frame, 1)

        self.stack = QStackedWidget()
        self.stack.setMinimumHeight(660)
        self.stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        content_layout.addWidget(self.stack, 1)

        self.config_tab = QWidget()
        self.request_tab = QWidget()
        self.config_tab.setMinimumHeight(650)
        self.request_tab.setMinimumHeight(650)
        self.stack.addWidget(self.config_tab)
        self.stack.addWidget(self.request_tab)
        self.config_tab_button.clicked.connect(lambda: self._switch_tab(0))
        self.request_tab_button.clicked.connect(lambda: self._switch_tab(1))
        self._build_config_tab()
        self._build_request_tab()
        self._switch_tab(0)

        menubar = self.menuBar()
        view_menu = menubar.addMenu("视图")
        reload_earth = QAction("重新加载 3D 地球", self)
        reload_earth.triggered.connect(self._reload_earth_panel)
        view_menu.addAction(reload_earth)

    def _make_earth_panel(self) -> QWidget:
        box = QFrame()
        box.setObjectName("earthFrame")
        layout = QVBoxLayout(box)
        layout.setContentsMargins(0, 0, 0, 0)
        if QWebEngineView is None:
            fallback = QLabel(
                "3D Earth WebView 未加载。\n请安装 PySide6 WebEngine 相关组件后重启。\n" + EARTH_URL
            )
            fallback.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fallback.setObjectName("earthFallback")
            layout.addWidget(fallback)
            return box
        self.earth_view = QWebEngineView()
        self.earth_view.setUrl(QUrl(EARTH_URL))
        self.earth_view.setFixedSize(310, 118)
        layout.addWidget(self.earth_view)
        box.setFixedSize(310, 118)
        return box

    def _reload_earth_panel(self) -> None:
        view = getattr(self, "earth_view", None)
        if view is not None:
            view.setUrl(QUrl(EARTH_URL))

    def _build_config_tab(self) -> None:
        layout = QVBoxLayout(self.config_tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)

        top = QGroupBox("服务与项目")
        top.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        top_layout = QGridLayout(top)
        layout.addWidget(top, 0)

        self.server_mode_combo = QComboBox()
        self.server_mode_combo.addItems(list(SERVER_MODES.keys()))
        self.server_mode_combo.currentTextChanged.connect(self._on_mode_changed)
        self.mode_hint_label = QLabel(SERVER_MODES["shared_port"])
        self.shared_port_edit = QLineEdit("8765")

        top_layout.addWidget(QLabel("服务模式"), 0, 0)
        top_layout.addWidget(self.server_mode_combo, 1, 0)
        top_layout.addWidget(self.mode_hint_label, 1, 1)
        top_layout.addWidget(QLabel("统一端口"), 0, 2)
        top_layout.addWidget(self.shared_port_edit, 1, 2)

        save_btn = QPushButton("保存配置")
        load_btn = QPushButton("加载配置")
        stop_btn = QPushButton("停止服务")
        start_btn = QPushButton("启动 / 重启本地服务")
        start_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self._save_project_config)
        load_btn.clicked.connect(self._load_project_config)
        stop_btn.clicked.connect(self._stop_servers_with_status)
        start_btn.clicked.connect(self._start_servers_from_config)
        top_layout.addWidget(save_btn, 1, 3)
        top_layout.addWidget(load_btn, 1, 4)
        top_layout.addWidget(stop_btn, 1, 5)
        top_layout.addWidget(start_btn, 1, 6)
        top_layout.setColumnStretch(1, 1)

        body = QSplitter(Qt.Orientation.Horizontal)
        body.setMinimumHeight(520)
        body.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(body, 1)

        sidebar = QGroupBox("接口列表")
        sidebar_layout = QVBoxLayout(sidebar)
        self.endpoint_listbox = QListWidget()
        self.endpoint_listbox.currentRowChanged.connect(self._on_endpoint_selected)
        sidebar_layout.addWidget(self.endpoint_listbox, 1)
        endpoint_btns = QHBoxLayout()
        for text, callback in [
            ("新增", self._add_endpoint),
            ("复制", self._duplicate_endpoint),
            ("删除", self._delete_endpoint),
        ]:
            btn = QPushButton(text)
            btn.clicked.connect(callback)
            endpoint_btns.addWidget(btn)
        sidebar_layout.addLayout(endpoint_btns)
        body.addWidget(sidebar)

        editor = QWidget()
        editor_layout = QVBoxLayout(editor)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        body.addWidget(editor)
        body.setStretchFactor(0, 1)
        body.setStretchFactor(1, 5)

        endpoint_box = QGroupBox("接口配置")
        endpoint_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        endpoint_layout = QGridLayout(endpoint_box)
        editor_layout.addWidget(endpoint_box, 0)

        self.endpoint_name_edit = QLineEdit()
        self.endpoint_method_combo = QComboBox()
        self.endpoint_method_combo.addItems(HTTP_METHODS)
        self.endpoint_path_edit = QLineEdit()
        self.endpoint_port_edit = QLineEdit()
        apply_btn = QPushButton("应用接口修改")
        apply_btn.clicked.connect(self._apply_endpoint_edit)

        endpoint_layout.addWidget(QLabel("接口名称"), 0, 0)
        endpoint_layout.addWidget(self.endpoint_name_edit, 1, 0)
        endpoint_layout.addWidget(QLabel("请求方式"), 0, 1)
        endpoint_layout.addWidget(self.endpoint_method_combo, 1, 1)
        endpoint_layout.addWidget(QLabel("API 路径"), 0, 2)
        endpoint_layout.addWidget(self.endpoint_path_edit, 1, 2)
        endpoint_layout.addWidget(QLabel("独立端口"), 0, 3)
        endpoint_layout.addWidget(self.endpoint_port_edit, 1, 3)
        endpoint_layout.addWidget(apply_btn, 1, 4)
        endpoint_layout.setColumnStretch(2, 1)

        response_area = QSplitter(Qt.Orientation.Horizontal)
        response_area.setMinimumHeight(410)
        response_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        editor_layout.addWidget(response_area, 1)

        case_panel = QGroupBox("条件响应")
        case_panel.setMinimumWidth(260)
        case_panel.setMinimumHeight(390)
        case_layout = QVBoxLayout(case_panel)
        case_layout.setContentsMargins(10, 14, 10, 10)
        case_layout.setSpacing(10)
        self.case_listbox = QListWidget()
        self.case_listbox.currentRowChanged.connect(self._on_case_selected)
        case_layout.addWidget(self.case_listbox, 1)
        case_btns = QHBoxLayout()
        for text, callback in [
            ("新增", self._add_case),
            ("复制", self._duplicate_case),
            ("删除", self._delete_case),
        ]:
            btn = QPushButton(text)
            btn.clicked.connect(callback)
            case_btns.addWidget(btn)
        case_layout.addLayout(case_btns)

        case_detail = QGroupBox("当前响应条件")
        case_detail.setMinimumHeight(210)
        case_detail.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        case_detail_layout = QFormLayout(case_detail)
        case_detail_layout.setContentsMargins(12, 16, 12, 12)
        case_detail_layout.setVerticalSpacing(10)
        self.case_name_edit = QLineEdit()
        self.case_status_edit = QLineEdit("200")
        self.match_text = QTextEdit()
        self.match_text.setMinimumHeight(76)
        self.match_text.setMaximumHeight(96)
        self.match_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.match_text.setPlainText("{}")
        case_detail_layout.addRow("响应名称", self.case_name_edit)
        case_detail_layout.addRow("状态码", self.case_status_edit)
        case_detail_layout.addRow("匹配条件 JSON", self.match_text)
        case_layout.addWidget(case_detail, 0)
        response_area.addWidget(case_panel)

        tree_panel = QGroupBox("响应假数据结构（树形）")
        tree_layout = QVBoxLayout(tree_panel)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("JSON 树结构（IDE 风格）")
        self.tree.itemDoubleClicked.connect(lambda _item, _col: self._edit_selected_node())
        self.tree.currentItemChanged.connect(lambda _cur, _prev: self._refresh_preview())
        tree_layout.addWidget(self.tree, 1)
        tree_btns = QHBoxLayout()
        for text, callback in [
            ("➕ 添加子节点", self._add_child_node),
            ("✏️ 编辑节点", self._edit_selected_node),
            ("🗑 删除节点", self._delete_selected_node),
            ("重置示例", self._reset_default_tree),
        ]:
            btn = QPushButton(text)
            btn.clicked.connect(callback)
            tree_btns.addWidget(btn)
        tree_layout.addLayout(tree_btns)
        response_area.addWidget(tree_panel)

        meta_panel = QWidget()
        meta_layout = QVBoxLayout(meta_panel)
        meta_layout.setContentsMargins(0, 0, 0, 0)
        self.headers_text = self._new_text_group(meta_layout, "响应头（JSON）", height=105)
        self.mock_params_text = self._new_text_group(meta_layout, "请求参数说明（JSON，可选，仅作为配置留档）", height=90)
        self.preview_text = self._new_text_group(meta_layout, "当前响应预览", height=180)
        export_btns = QHBoxLayout()
        for text, callback in [
            ("导入 JSON 模板", self._import_response_template),
            ("导出 JSON 模板", self._export_response_template),
            ("复制响应 JSON", self._copy_response_json),
        ]:
            btn = QPushButton(text)
            btn.clicked.connect(callback)
            export_btns.addWidget(btn)
        export_btns.addStretch(1)
        meta_layout.addLayout(export_btns)
        response_area.addWidget(meta_panel)
        response_area.setStretchFactor(0, 1)
        response_area.setStretchFactor(1, 3)
        response_area.setStretchFactor(2, 2)
        response_area.setChildrenCollapsible(False)
        self._on_mode_changed()

    def _switch_tab(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        self.config_tab_button.setChecked(index == 0)
        self.request_tab_button.setChecked(index == 1)

    def _new_text_group(self, parent_layout: QVBoxLayout, title: str, height: int) -> QTextEdit:
        # 使用“标题 QLabel + 内容 QTextEdit”的轻量面板，避免 QGroupBox 标题预留大块空白。
        panel = QFrame()
        panel.setObjectName("plainPanel")
        panel.setMinimumHeight(0)
        panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(10, 8, 10, 10)
        panel_layout.setSpacing(6)

        label = QLabel(title)
        label.setObjectName("panelTitle")
        panel_layout.addWidget(label, 0)

        text = QTextEdit()
        text.setMinimumHeight(42)
        text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        panel_layout.addWidget(text, 1)
        parent_layout.addWidget(panel, 1)
        return text

    def _build_request_tab(self) -> None:
        layout = QVBoxLayout(self.request_tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)

        top = QGroupBox("请求配置")
        top.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        top_layout = QGridLayout(top)
        layout.addWidget(top, 0)
        self.req_method_combo = QComboBox()
        self.req_method_combo.addItems(HTTP_METHODS)
        self.req_url_edit = QLineEdit("http://127.0.0.1:8765/api/mock")
        sync_btn = QPushButton("使用选中接口")
        sync_btn.clicked.connect(self._sync_request_tab_from_current_endpoint)
        top_layout.addWidget(QLabel("请求方式"), 0, 0)
        top_layout.addWidget(self.req_method_combo, 1, 0)
        top_layout.addWidget(QLabel("请求 URL（含端口）"), 0, 1)
        top_layout.addWidget(self.req_url_edit, 1, 1)
        top_layout.addWidget(sync_btn, 1, 2)
        top_layout.setColumnStretch(1, 1)

        center = QSplitter(Qt.Orientation.Horizontal)
        center.setMinimumHeight(520)
        center.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(center, 1)
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        self.req_headers_text = self._new_text_group(left_layout, "请求头（JSON）", height=140)
        self.req_headers_text.setPlainText(pretty_json(DEFAULT_REQUEST_HEADERS))
        self.req_params_text = self._new_text_group(left_layout, "请求参数 / Body（JSON，可选）", height=260)
        self.req_params_text.setPlainText(pretty_json({"page": 1, "pageSize": 10}))
        center.addWidget(left)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        self.result_text = self._new_text_group(right_layout, "请求结果（自动格式化）", height=400)
        center.addWidget(right)
        center.setStretchFactor(0, 2)
        center.setStretchFactor(1, 3)
        center.setChildrenCollapsible(False)

        bottom = QHBoxLayout()
        bottom.addStretch(1)
        send_btn = QPushButton("开始请求")
        send_btn.setObjectName("primaryButton")
        send_btn.clicked.connect(self._send_request)
        bottom.addWidget(send_btn)
        layout.addLayout(bottom)

    def _on_mode_changed(self) -> None:
        mode = self.server_mode_combo.currentText() if hasattr(self, "server_mode_combo") else "shared_port"
        if hasattr(self, "mode_hint_label"):
            self.mode_hint_label.setText(SERVER_MODES.get(mode, ""))
        if hasattr(self, "shared_port_edit"):
            self.shared_port_edit.setEnabled(mode == "shared_port")
        if hasattr(self, "endpoint_port_edit"):
            self.endpoint_port_edit.setEnabled(mode == "per_endpoint_port")
        if hasattr(self, "endpoint_listbox"):
            self._refresh_endpoint_list(select_id=self.current_endpoint_id, save_current=False)

    def _endpoint_label(self, endpoint: EndpointConfig) -> str:
        if self.server_mode_combo.currentText() == "shared_port":
            return f"{endpoint.name}    {endpoint.method} {endpoint.path}"
        return f"{endpoint.name}    {endpoint.method} http://127.0.0.1:{endpoint.port}{endpoint.path}"

    def _refresh_endpoint_list(self, select_id: Optional[str] = None, save_current: bool = True) -> None:
        if save_current:
            self._save_current_endpoint_from_widgets()
        self._loading = True
        self.endpoint_listbox.clear()
        for endpoint in self.endpoints:
            self.endpoint_listbox.addItem(QListWidgetItem(self._endpoint_label(endpoint)))
        idx_to_select = 0
        if select_id:
            for idx, endpoint in enumerate(self.endpoints):
                if endpoint.endpoint_id == select_id:
                    idx_to_select = idx
                    break
        if self.endpoints:
            self.endpoint_listbox.setCurrentRow(idx_to_select)
            self._load_endpoint(self.endpoints[idx_to_select])
        self._loading = False

    def _refresh_case_list(self, endpoint: EndpointConfig, select_id: Optional[str] = None, save_current: bool = True) -> None:
        if save_current:
            self._save_current_case_from_widgets()
        self._loading = True
        self.case_listbox.clear()
        for case in endpoint.cases:
            condition = case.match_text.strip()
            tag = "默认" if condition in {"", "{}"} else "条件"
            self.case_listbox.addItem(QListWidgetItem(f"{case.name}    [{tag}] HTTP {case.status_code}"))
        idx_to_select = 0
        if select_id:
            for idx, case in enumerate(endpoint.cases):
                if case.case_id == select_id:
                    idx_to_select = idx
                    break
        if endpoint.cases:
            self.case_listbox.setCurrentRow(idx_to_select)
            self._load_case(endpoint.cases[idx_to_select])
        self._loading = False

    def _on_endpoint_selected(self, row: int) -> None:
        if self._loading or row < 0:
            return
        self._save_current_endpoint_from_widgets()
        self._load_endpoint(self.endpoints[row])

    def _on_case_selected(self, row: int) -> None:
        if self._loading or row < 0:
            return
        endpoint = self._get_current_endpoint()
        if not endpoint:
            return
        self._save_current_case_from_widgets()
        self._load_case(endpoint.cases[row])

    def _get_current_endpoint(self) -> Optional[EndpointConfig]:
        if not self.current_endpoint_id:
            return None
        for endpoint in self.endpoints:
            if endpoint.endpoint_id == self.current_endpoint_id:
                return endpoint
        return None

    def _get_current_case(self) -> Optional[ResponseCase]:
        endpoint = self._get_current_endpoint()
        if not endpoint or not self.current_case_id:
            return None
        for case in endpoint.cases:
            if case.case_id == self.current_case_id:
                return case
        return None

    def _load_endpoint(self, endpoint: EndpointConfig) -> None:
        self.current_endpoint_id = endpoint.endpoint_id
        self.endpoint_name_edit.setText(endpoint.name)
        self.endpoint_method_combo.setCurrentText(endpoint.method)
        self.endpoint_path_edit.setText(endpoint.path)
        self.endpoint_port_edit.setText(endpoint.port)
        self.headers_text.setPlainText(endpoint.headers_text)
        self.mock_params_text.setPlainText(endpoint.params_text)
        selected_case_id = endpoint.cases[0].case_id if endpoint.cases else None
        self._refresh_case_list(endpoint, select_id=selected_case_id, save_current=False)

    def _load_case(self, case: ResponseCase) -> None:
        self.current_case_id = case.case_id
        self.case_name_edit.setText(case.name)
        self.case_status_edit.setText(str(case.status_code))
        self.match_text.setPlainText(case.match_text or "{}")
        self.root_node = case.root_node
        self._refresh_tree()
        self._refresh_preview()

    def _save_current_case_from_widgets(self) -> None:
        case = self._get_current_case()
        if not case:
            return
        case.name = self.case_name_edit.text().strip() or "未命名响应"
        try:
            case.status_code = parse_status_code(self.case_status_edit.text())
        except Exception:
            pass
        case.match_text = self.match_text.toPlainText().strip() or "{}"
        case.root_node = self.root_node

    def _save_current_endpoint_from_widgets(self) -> None:
        endpoint = self._get_current_endpoint()
        if not endpoint:
            return
        self._save_current_case_from_widgets()
        endpoint.name = self.endpoint_name_edit.text().strip() or "未命名接口"
        endpoint.method = self.endpoint_method_combo.currentText().strip().upper() or "GET"
        endpoint.path = normalize_path(self.endpoint_path_edit.text())
        endpoint.port = self.endpoint_port_edit.text().strip() or "8765"
        endpoint.headers_text = self.headers_text.toPlainText().strip() or "{}"
        endpoint.params_text = self.mock_params_text.toPlainText().strip()

    def _apply_endpoint_edit(self) -> None:
        try:
            self._save_current_endpoint_from_widgets()
            endpoint = self._get_current_endpoint()
            if not endpoint:
                return
            parse_port(endpoint.port)
            parse_json_text(endpoint.headers_text, default={})
            for case in endpoint.cases:
                parse_status_code(case.status_code)
                condition = parse_json_text(case.match_text, default={})
                if not isinstance(condition, dict):
                    raise ValueError("匹配条件 JSON 必须是字典，例如 {\"page\": 2}")
        except Exception as exc:
            QMessageBox.critical(self, "配置错误", str(exc))
            return
        self._refresh_endpoint_list(select_id=self.current_endpoint_id, save_current=False)
        self._refresh_case_list(endpoint, select_id=self.current_case_id, save_current=False)
        self._sync_request_tab_from_current_endpoint()
        QMessageBox.information(self, "已应用", "当前接口配置已应用到界面。")

    def _add_endpoint(self) -> None:
        self._save_current_endpoint_from_widgets()
        endpoint = new_endpoint(len(self.endpoints) + 1)
        self.endpoints.append(endpoint)
        self._refresh_endpoint_list(select_id=endpoint.endpoint_id, save_current=False)

    def _duplicate_endpoint(self) -> None:
        self._save_current_endpoint_from_widgets()
        endpoint = self._get_current_endpoint()
        if not endpoint:
            return
        duplicated = endpoint_from_dict(endpoint_to_dict(endpoint))
        duplicated.name = endpoint.name + " 副本"
        self.endpoints.append(duplicated)
        self._refresh_endpoint_list(select_id=duplicated.endpoint_id, save_current=False)

    def _delete_endpoint(self) -> None:
        endpoint = self._get_current_endpoint()
        if not endpoint:
            return
        if len(self.endpoints) == 1:
            QMessageBox.information(self, "不能删除", "至少保留一个接口。")
            return
        ok = QMessageBox.question(self, "确认删除", f"确认删除接口：{endpoint.name}？")
        if ok != QMessageBox.StandardButton.Yes:
            return
        self.endpoints = [item for item in self.endpoints if item.endpoint_id != endpoint.endpoint_id]
        self.current_endpoint_id = None
        self.current_case_id = None
        self._refresh_endpoint_list(select_id=self.endpoints[0].endpoint_id, save_current=False)

    def _add_case(self) -> None:
        self._save_current_endpoint_from_widgets()
        endpoint = self._get_current_endpoint()
        if not endpoint:
            return
        case = new_response_case(f"条件响应 {len(endpoint.cases) + 1}", empty_success_tree())
        case.match_text = pretty_json({"page": len(endpoint.cases) + 1})
        endpoint.cases.append(case)
        self._refresh_case_list(endpoint, select_id=case.case_id, save_current=False)

    def _duplicate_case(self) -> None:
        self._save_current_endpoint_from_widgets()
        endpoint = self._get_current_endpoint()
        case = self._get_current_case()
        if not endpoint or not case:
            return
        duplicated = ResponseCase(
            case_id=uid(),
            name=case.name + " 副本",
            status_code=case.status_code,
            match_text=case.match_text,
            root_node=clone_node(case.root_node),
        )
        endpoint.cases.append(duplicated)
        self._refresh_case_list(endpoint, select_id=duplicated.case_id, save_current=False)

    def _delete_case(self) -> None:
        endpoint = self._get_current_endpoint()
        case = self._get_current_case()
        if not endpoint or not case:
            return
        if len(endpoint.cases) == 1:
            QMessageBox.information(self, "不能删除", "每个接口至少保留一个响应。")
            return
        ok = QMessageBox.question(self, "确认删除", f"确认删除响应：{case.name}？")
        if ok != QMessageBox.StandardButton.Yes:
            return
        endpoint.cases = [item for item in endpoint.cases if item.case_id != case.case_id]
        self.current_case_id = None
        self._refresh_case_list(endpoint, select_id=endpoint.cases[0].case_id, save_current=False)

    def _refresh_tree(self) -> None:
        self.tree.clear()
        self.node_map.clear()
        root_item = self._insert_node(None, self.root_node, is_root=True)
        self.tree.setCurrentItem(root_item)
        self.tree.expandAll()

    def _insert_node(
        self,
        parent_item: Optional[QTreeWidgetItem],
        node: DataNode,
        is_root: bool = False,
        index: Optional[int] = None,
    ) -> QTreeWidgetItem:
        self.node_map[node.node_id] = node
        item = QTreeWidgetItem([format_node_label(node, is_root=is_root, index=index)])
        item.setData(0, Qt.ItemDataRole.UserRole, node.node_id)
        if parent_item is None:
            self.tree.addTopLevelItem(item)
        else:
            parent_item.addChild(item)
        for idx, child in enumerate(node.children):
            self._insert_node(item, child, is_root=False, index=idx)
        return item

    def _get_selected_node(self) -> DataNode:
        item = self.tree.currentItem()
        if not item:
            return self.root_node
        node_id = item.data(0, Qt.ItemDataRole.UserRole)
        return self.node_map.get(str(node_id), self.root_node)

    def _find_parent(self, current: DataNode, target_id: str) -> Optional[DataNode]:
        for child in current.children:
            if child.node_id == target_id:
                return current
            found = self._find_parent(child, target_id)
            if found:
                return found
        return None

    def _add_child_node(self) -> None:
        parent = self._get_selected_node()
        if not parent.is_container():
            QMessageBox.information(self, "不能继续拓展", "只有字典和数组容器节点可以继续添加下一代。")
            return
        dialog = NodeDialog(self, "添加子节点", parent_type=parent.node_type, node_type="string")
        if dialog.exec() != QDialog.DialogCode.Accepted or not dialog.result_data:
            return
        key = dialog.result_data["key"] if parent.node_type == "dict" else ""
        child = new_node(key, dialog.result_data["node_type"], dialog.result_data["value"])
        parent.children.append(child)
        self._refresh_tree()
        self._select_tree_node(child.node_id)
        self._refresh_preview()

    def _select_tree_node(self, node_id: str) -> None:
        def walk(item: QTreeWidgetItem) -> bool:
            if str(item.data(0, Qt.ItemDataRole.UserRole)) == node_id:
                self.tree.setCurrentItem(item)
                return True
            for i in range(item.childCount()):
                if walk(item.child(i)):
                    return True
            return False

        for i in range(self.tree.topLevelItemCount()):
            if walk(self.tree.topLevelItem(i)):
                return

    def _edit_selected_node(self) -> None:
        node = self._get_selected_node()
        if node.node_id == self.root_node.node_id:
            parent_type = "dict"
            allow_key_edit = False
        else:
            parent = self._find_parent(self.root_node, node.node_id)
            parent_type = parent.node_type if parent else "dict"
            allow_key_edit = parent_type != "list"
        old_type = node.node_type
        dialog = NodeDialog(
            self,
            "编辑节点",
            parent_type=parent_type,
            key=node.key,
            node_type=node.node_type,
            value=node.value,
            allow_key_edit=allow_key_edit,
        )
        if dialog.exec() != QDialog.DialogCode.Accepted or not dialog.result_data:
            return
        if old_type in CONTAINER_TYPES and dialog.result_data["node_type"] not in CONTAINER_TYPES and node.children:
            ok = QMessageBox.question(self, "确认改变类型", "改成裸数据后，该节点下的所有子节点都会被删除。确认继续吗？")
            if ok != QMessageBox.StandardButton.Yes:
                return
            node.children.clear()
        node.key = dialog.result_data["key"] if allow_key_edit else node.key
        if parent_type == "list":
            node.key = ""
        node.node_type = dialog.result_data["node_type"]
        node.value = dialog.result_data["value"]
        self._refresh_tree()
        self._select_tree_node(node.node_id)
        self._refresh_preview()

    def _delete_selected_node(self) -> None:
        node = self._get_selected_node()
        if node.node_id == self.root_node.node_id:
            QMessageBox.information(self, "不能删除原点", "原点是响应数据的起始节点，不能删除。")
            return
        parent = self._find_parent(self.root_node, node.node_id)
        if not parent:
            return
        ok = QMessageBox.question(self, "确认删除", "删除后该节点及所有子节点都会消失。确认删除吗？")
        if ok != QMessageBox.StandardButton.Yes:
            return
        parent.children = [child for child in parent.children if child.node_id != node.node_id]
        self._refresh_tree()
        self._refresh_preview()

    def _reset_default_tree(self) -> None:
        ok = QMessageBox.question(self, "重置示例", "确认用内置示例覆盖当前响应的假数据结构吗？")
        if ok != QMessageBox.StandardButton.Yes:
            return
        case = self._get_current_case()
        self.root_node = default_tree()
        if case:
            case.root_node = self.root_node
        self._refresh_tree()
        self._refresh_preview()

    def _refresh_preview(self) -> None:
        try:
            data = node_to_python(self.root_node)
            content = pretty_json(data)
        except Exception as exc:
            content = f"预览失败：{exc}\n\n{traceback.format_exc()}"
        self.preview_text.setPlainText(content)

    def _project_to_dict(self) -> Dict[str, Any]:
        self._save_current_endpoint_from_widgets()
        return {
            "app": APP_NAME,
            "version": APP_VERSION,
            "server_mode": self.server_mode_combo.currentText(),
            "shared_port": self.shared_port_edit.text(),
            "earth_url": EARTH_URL,
            "endpoints": [endpoint_to_dict(endpoint) for endpoint in self.endpoints],
        }

    def _load_project_dict(self, data: Dict[str, Any]) -> None:
        self._stop_servers()
        mode = data.get("server_mode", "shared_port")
        if mode not in SERVER_MODES:
            mode = "shared_port"
        self.server_mode_combo.setCurrentText(mode)
        self.shared_port_edit.setText(str(data.get("shared_port", "8765")))
        endpoints = [endpoint_from_dict(item) for item in data.get("endpoints", [])]
        if not endpoints:
            endpoints = [new_endpoint(1)]
        self.endpoints = endpoints
        self.current_endpoint_id = None
        self.current_case_id = None
        self._on_mode_changed()
        self._refresh_endpoint_list(select_id=self.endpoints[0].endpoint_id, save_current=False)
        self.status_label.setText("已加载配置，服务未启动")

    def _save_project_config(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "保存 Mock 配置", "jobs_mock_tool_config.json", "JSON 文件 (*.json);;所有文件 (*.*)")
        if not path:
            return
        try:
            data = self._project_to_dict()
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "保存成功", f"配置已保存：\n{path}")
        except Exception as exc:
            QMessageBox.critical(self, "保存失败", str(exc))

    def _load_project_config(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "加载 Mock 配置", "", "JSON 文件 (*.json);;所有文件 (*.*)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("配置文件格式不正确")
            self._load_project_dict(data)
            QMessageBox.information(self, "加载成功", f"配置已加载：\n{path}")
        except Exception as exc:
            QMessageBox.critical(self, "加载失败", str(exc))

    def _import_response_template(self) -> None:
        case = self._get_current_case()
        if not case:
            return
        path, _ = QFileDialog.getOpenFileName(self, "导入响应 JSON 模板", "", "JSON 文件 (*.json);;所有文件 (*.*)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            root = python_to_node(data, "root")
            case.root_node = root
            self.root_node = root
            self._refresh_tree()
            self._refresh_preview()
            QMessageBox.information(self, "导入成功", "JSON 模板已转换为树形结构。")
        except Exception as exc:
            QMessageBox.critical(self, "导入失败", str(exc))

    def _export_response_template(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "导出响应 JSON 模板", "response_template.json", "JSON 文件 (*.json);;所有文件 (*.*)")
        if not path:
            return
        try:
            data = node_to_python(self.root_node)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "导出成功", f"响应模板已导出：\n{path}")
        except Exception as exc:
            QMessageBox.critical(self, "导出失败", str(exc))

    def _copy_response_json(self) -> None:
        try:
            data = pretty_json(node_to_python(self.root_node))
            QApplication.clipboard().setText(data)
            QMessageBox.information(self, "已复制", "当前响应 JSON 已复制到剪贴板。")
        except Exception as exc:
            QMessageBox.critical(self, "复制失败", str(exc))

    def _build_runtime_by_port(self) -> Dict[int, Dict[Tuple[str, str], Dict[str, Any]]]:
        self._save_current_endpoint_from_widgets()
        mode = self.server_mode_combo.currentText()
        if mode == "shared_port":
            shared_port = parse_port(self.shared_port_edit.text())
        runtime_by_port: Dict[int, Dict[Tuple[str, str], Dict[str, Any]]] = {}
        seen: set[Tuple[int, str, str]] = set()

        for endpoint in self.endpoints:
            method = endpoint.method.strip().upper()
            path = normalize_path(endpoint.path)
            port = shared_port if mode == "shared_port" else parse_port(endpoint.port)
            route_key = (port, method, path)
            if route_key in seen:
                raise ValueError(f"接口冲突：端口 {port} 下已经存在 {method} {path}")
            seen.add(route_key)

            headers = parse_json_text(endpoint.headers_text, default={})
            if not isinstance(headers, dict):
                raise ValueError(f"{endpoint.name} 的响应头必须是 JSON 字典")
            headers = {str(k): str(v) for k, v in headers.items()}

            runtime_cases: List[Dict[str, Any]] = []
            for case in endpoint.cases:
                status_code = parse_status_code(case.status_code)
                condition = parse_json_text(case.match_text, default={})
                if not isinstance(condition, dict):
                    raise ValueError(f"{endpoint.name} / {case.name} 的匹配条件必须是 JSON 字典")
                runtime_cases.append(
                    {
                        "name": case.name,
                        "status_code": status_code,
                        "match": condition,
                        "response_data": node_to_python(case.root_node),
                    }
                )
            if not runtime_cases:
                runtime_cases.append(
                    {
                        "name": "默认响应",
                        "status_code": 200,
                        "match": {},
                        "response_data": {"message": "ok"},
                    }
                )

            runtime_by_port.setdefault(port, {})[(method, path)] = {
                "endpoint_name": endpoint.name,
                "headers": headers,
                "cases": runtime_cases,
            }
        return runtime_by_port

    def _start_servers_from_config(self) -> None:
        try:
            runtime_by_port = self._build_runtime_by_port()
        except Exception as exc:
            QMessageBox.critical(self, "配置错误", str(exc))
            return

        self._stop_servers()
        started: List[str] = []
        try:
            for port, route_map in runtime_by_port.items():
                server = ThreadingHTTPServer(("127.0.0.1", port), MockRequestHandler)
                server.route_map = route_map
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                self.servers[port] = server
                self.server_threads[port] = thread
                started.append(f"http://127.0.0.1:{port}  ({len(route_map)} 个接口)")
        except OSError as exc:
            self._stop_servers()
            QMessageBox.critical(self, "端口启动失败", f"端口无法使用：{exc}")
            return
        except Exception as exc:
            self._stop_servers()
            QMessageBox.critical(self, "启动失败", str(exc))
            return

        routes_count = sum(len(route_map) for route_map in runtime_by_port.values())
        self.status_label.setText(f"服务已启动：{len(runtime_by_port)} 个端口，{routes_count} 个接口")
        self._refresh_endpoint_list(select_id=self.current_endpoint_id, save_current=False)
        self._sync_request_tab_from_current_endpoint()
        QMessageBox.information(self, "服务已启动", "本地数据服务已启动：\n" + "\n".join(started))

    def _stop_servers(self) -> None:
        for server in list(self.servers.values()):
            try:
                server.shutdown()
                server.server_close()
            except Exception:
                pass
        self.servers.clear()
        self.server_threads.clear()

    def _stop_servers_with_status(self) -> None:
        self._stop_servers()
        self.status_label.setText("服务已停止")
        QMessageBox.information(self, "服务已停止", "所有本地 Mock 服务已停止。")

    def _sync_request_tab_from_current_endpoint(self) -> None:
        self._save_current_endpoint_from_widgets()
        endpoint = self._get_current_endpoint()
        if not endpoint:
            return
        try:
            if self.server_mode_combo.currentText() == "shared_port":
                port = parse_port(self.shared_port_edit.text())
            else:
                port = parse_port(endpoint.port)
        except Exception:
            port = 8765
        path = normalize_path(endpoint.path)
        self.req_method_combo.setCurrentText(endpoint.method.strip().upper() or "GET")
        self.req_url_edit.setText(f"http://127.0.0.1:{port}{path}")

    def _read_request_headers(self) -> Dict[str, str]:
        headers = parse_json_text(self.req_headers_text.toPlainText(), default={})
        if headers is None:
            return {}
        if not isinstance(headers, dict):
            raise ValueError("请求头必须是 JSON 字典")
        return {str(k): str(v) for k, v in headers.items()}

    def _read_request_params(self) -> Any:
        raw = self.req_params_text.toPlainText().strip()
        if not raw:
            return None
        return json.loads(raw)

    def _append_query_params(self, url: str, params: Any) -> str:
        if not params:
            return url
        if not isinstance(params, dict):
            raise ValueError("GET 请求参数建议填写 JSON 字典")
        parsed = urllib.parse.urlparse(url)
        old_pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
        old_qs = single_or_list_dict(old_pairs)
        merged = {**old_qs, **params}
        query = urllib.parse.urlencode(merged, doseq=True)
        return urllib.parse.urlunparse(parsed._replace(query=query))

    def _send_request(self) -> None:
        method = self.req_method_combo.currentText().strip().upper() or "GET"
        url = self.req_url_edit.text().strip()
        if not url:
            QMessageBox.warning(self, "URL 为空", "请先填写请求 URL。")
            return
        try:
            headers = self._read_request_headers()
            params = self._read_request_params()
            data: Optional[bytes] = None
            request_url = url
            if method == "GET":
                request_url = self._append_query_params(url, params)
            elif params is not None:
                data = pretty_json(params).encode("utf-8")
                headers.setdefault("Content-Type", "application/json; charset=utf-8")
            req = urllib.request.Request(request_url, data=data, headers=headers, method=method)
            with urllib.request.urlopen(req, timeout=10) as resp:
                body_bytes = resp.read()
                status = resp.status
                resp_headers = dict(resp.headers.items())
            body_text = body_bytes.decode("utf-8", errors="replace")
            formatted_body = self._format_response_body(body_text)
            result = [
                f"HTTP {status}",
                "",
                "[Response Headers]",
                pretty_json(resp_headers),
                "",
                "[Response Body]",
                formatted_body,
            ]
            self.result_text.setPlainText("\n".join(result))
        except urllib.error.HTTPError as exc:
            body_text = exc.read().decode("utf-8", errors="replace")
            result = [
                f"HTTP {exc.code}",
                "",
                "[Error Body]",
                self._format_response_body(body_text),
            ]
            self.result_text.setPlainText("\n".join(result))
        except Exception as exc:
            self.result_text.setPlainText(f"请求失败：{exc}\n\n{traceback.format_exc()}")

    def _format_response_body(self, body_text: str) -> str:
        try:
            data = json.loads(body_text)
            return pretty_json(data)
        except Exception:
            return body_text

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        choice = QMessageBox.question(
            self,
            "关闭 JobsMockTool",
            "是否最小化到任务栏并继续运行？\n\n选择“否”将停止本地 Mock 服务并退出程序。",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Yes,
        )
        if choice == QMessageBox.StandardButton.Yes:
            event.ignore()
            if self.tray_icon is not None and self.tray_icon.isVisible():
                self.hide()
            else:
                self.showMinimized()
            return
        if choice == QMessageBox.StandardButton.No:
            self._stop_servers()
            event.accept()
            return
        event.ignore()


STYLE_SHEET = """
QMainWindow, QWidget {
    background: #f4f6fb;
    color: #111827;
    font-family: Arial, "Microsoft YaHei", sans-serif;
    font-size: 14px;
}
QMenuBar, QMenu {
    background: #ffffff;
    color: #111827;
}
#headerFrame {
    background: #f4f6fb;
}
#titleLabel {
    font-size: 18px;
    font-weight: 700;
    color: #111827;
}
#subtitleLabel {
    color: #6b7280;
}
#metaLabel {
    color: #374151;
    font-size: 13px;
}
#statusLabel {
    color: #2563eb;
    font-weight: 700;
}
#mutedLabel {
    color: #6b7280;
}
QLabel {
    background: transparent;
}
#contentFrame {
    background: #f4f6fb;
    border: 2px solid #111111;
    border-radius: 0px;
}
#plainPanel {
    background: #ffffff;
    border: 1px solid #d6dbe6;
    border-radius: 6px;
}
#panelTitle {
    background: transparent;
    color: #111827;
    font-weight: 700;
    padding: 0px;
}
#earthFrame {
    background: #030712;
    border: 1px solid #d6dbe6;
    border-radius: 8px;
    min-width: 310px;
    max-width: 310px;
    min-height: 118px;
    max-height: 118px;
}
#earthFallback {
    background: #030712;
    color: #93c5fd;
    border-radius: 8px;
}
QGroupBox {
    background: #ffffff;
    border: 1px solid #d6dbe6;
    border-radius: 6px;
    margin-top: 8px;
    padding-top: 8px;
    font-weight: 700;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
    color: #111827;
    background: transparent;
}
QLineEdit, QTextEdit, QComboBox, QListWidget, QTreeWidget {
    background: #ffffff;
    color: #111111;
    border: 1px solid #cbd5e1;
    border-radius: 3px;
    selection-background-color: #dbeafe;
    selection-color: #111111;
}
QLineEdit, QComboBox {
    min-height: 30px;
    padding: 4px 6px;
}
QTextEdit {
    padding: 8px;
    font-family: Menlo, Consolas, "Courier New", monospace;
    font-size: 13px;
}
QTreeWidget::item, QListWidget::item {
    min-height: 26px;
    color: #111111;
}
QTreeWidget::item:selected, QListWidget::item:selected {
    background: #dbeafe;
    color: #111111;
}
QPushButton {
    background: #f3f4f6;
    color: #111827;
    border: 1px solid #d1d5db;
    border-radius: 5px;
    padding: 7px 11px;
}
QPushButton:hover {
    background: #e5e7eb;
}
QPushButton:disabled {
    color: #9ca3af;
    background: #f3f4f6;
}
#primaryButton {
    background: #dbeafe;
    border-color: #93c5fd;
    font-weight: 700;
}
#primaryButton:hover {
    background: #bfdbfe;
}
#customTabBar {
    background: #f4f6fb;
}
#tabButton {
    background: #e5e7eb;
    color: #374151;
    border: 1px solid #cbd5e1;
    border-bottom: none;
    border-radius: 0;
    padding: 12px 22px;
    font-weight: 500;
}
#tabButton:checked {
    background: #ffffff;
    color: #111827;
    font-weight: 700;
}
#tabButton:hover {
    background: #eef2f7;
}

QTabWidget::pane {
    border: 1px solid #cbd5e1;
    background: #f4f6fb;
}
QTabBar {
    qproperty-expanding: false;
    alignment: left;
}
QTabBar::tab {
    background: #e5e7eb;
    color: #374151;
    border: 1px solid #cbd5e1;
    padding: 10px 20px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background: #ffffff;
    color: #111827;
    font-weight: 700;
    padding: 13px 28px;
}
QSplitter::handle {
    background: #e5e7eb;
}
"""


def main() -> None:
    app = QApplication([])
    window = JobsMockTool()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
