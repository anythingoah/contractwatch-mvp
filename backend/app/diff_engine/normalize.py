"""
Turns a raw REST (OpenAPI) or MCP contract into ONE canonical shape so the
diff engine never has to know which source it came from.

Canonical shape:
{
  "operations": {
      "<method> <path>" | "<tool_name>": {
          "required_params": {name: type_str, ...},
          "optional_params": {name: type_str, ...},
          "description": str,
      },
      ...
  }
}

Only structural fields are kept. Anything purely cosmetic (key order, spacing,
$ref style) is discarded before this shape is built, which is what makes the
diff resistant to false positives.
"""
from typing import Any


def _schema_type(schema: dict) -> str:
    """Best-effort JSON-schema type extraction, defaults to 'any'."""
    if not isinstance(schema, dict):
        return "any"
    return schema.get("type", "any")


def normalize_openapi(spec: dict) -> dict:
    """Normalize a parsed OpenAPI (2.0 or 3.x) document."""
    operations: dict[str, Any] = {}
    paths = spec.get("paths", {}) or {}

    for path, methods in paths.items():
        if not isinstance(methods, dict):
            continue
        for method, op in methods.items():
            if method.lower() not in ("get", "post", "put", "patch", "delete"):
                continue
            if not isinstance(op, dict):
                continue

            key = f"{method.upper()} {path}"
            required: dict[str, str] = {}
            optional: dict[str, str] = {}

            for param in op.get("parameters", []) or []:
                if not isinstance(param, dict):
                    continue
                name = param.get("name")
                if not name:
                    continue
                p_type = _schema_type(param.get("schema", {}))
                if param.get("required"):
                    required[name] = p_type
                else:
                    optional[name] = p_type

            # Request body fields (OpenAPI 3.x)
            body = (
                op.get("requestBody", {})
                .get("content", {})
                .get("application/json", {})
                .get("schema", {})
            )
            body_required = set(body.get("required", []) or [])
            for field, field_schema in (body.get("properties", {}) or {}).items():
                f_type = _schema_type(field_schema)
                if field in body_required:
                    required[field] = f_type
                else:
                    optional[field] = f_type

            operations[key] = {
                "required_params": required,
                "optional_params": optional,
                "description": op.get("summary") or op.get("description") or "",
            }

    return {"operations": operations}


def normalize_mcp(tools_response: dict) -> dict:
    """Normalize an MCP `tools/list` response."""
    operations: dict[str, Any] = {}
    tools = tools_response.get("tools", []) or []

    for tool in tools:
        if not isinstance(tool, dict):
            continue
        name = tool.get("name")
        if not name:
            continue

        input_schema = tool.get("inputSchema", {}) or {}
        properties = input_schema.get("properties", {}) or {}
        required_names = set(input_schema.get("required", []) or [])

        required: dict[str, str] = {}
        optional: dict[str, str] = {}
        for field, field_schema in properties.items():
            f_type = _schema_type(field_schema)
            if field in required_names:
                required[field] = f_type
            else:
                optional[field] = f_type

        operations[name] = {
            "required_params": required,
            "optional_params": optional,
            "description": tool.get("description") or "",
        }

    return {"operations": operations}
