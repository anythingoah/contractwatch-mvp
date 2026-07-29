"""
Fixture-based tests for the diff engine. Each test is a before/after pair
mirroring a real-world contract change, matching the examples in the product
spec (removed required MCP param, REST field type change, etc).
"""
from app.diff_engine.engine import diff_contracts, overall_severity, is_breaking
from app.diff_engine.normalize import normalize_openapi, normalize_mcp


def test_mcp_removed_required_parameter_is_critical():
    before = normalize_mcp({
        "tools": [{
            "name": "create_invoice",
            "description": "Create an invoice",
            "inputSchema": {
                "properties": {"amount": {"type": "number"}, "currency": {"type": "string"}},
                "required": ["amount", "currency"],
            },
        }]
    })
    after = normalize_mcp({
        "tools": [{
            "name": "create_invoice",
            "description": "Create an invoice",
            "inputSchema": {
                "properties": {"amount": {"type": "number"}},
                "required": ["amount"],
            },
        }]
    })

    changes = diff_contracts(before, after)
    assert is_breaking(changes)
    assert overall_severity(changes) == "critical"
    assert any(c["type"] == "removed_parameter" and "currency" in c["message"] for c in changes)


def test_rest_type_change_is_critical():
    before = normalize_openapi({
        "paths": {
            "/users/{id}": {
                "get": {
                    "parameters": [{"name": "email", "required": True, "schema": {"type": "string"}}]
                }
            }
        }
    })
    after = normalize_openapi({
        "paths": {
            "/users/{id}": {
                "get": {
                    "parameters": [{"name": "email", "required": True, "schema": {"type": "integer"}}]
                }
            }
        }
    })

    changes = diff_contracts(before, after)
    assert is_breaking(changes)
    assert any(c["type"] == "type_changed" for c in changes)


def test_removed_endpoint_is_critical():
    before = normalize_openapi({"paths": {"/users/{id}": {"delete": {}}}})
    after = normalize_openapi({"paths": {}})

    changes = diff_contracts(before, after)
    assert is_breaking(changes)
    assert changes[0]["type"] == "removed_endpoint"


def test_new_optional_field_is_informational_only():
    before = normalize_mcp({
        "tools": [{"name": "search", "inputSchema": {"properties": {"q": {"type": "string"}}, "required": ["q"]}}]
    })
    after = normalize_mcp({
        "tools": [{"name": "search", "inputSchema": {
            "properties": {"q": {"type": "string"}, "limit": {"type": "integer"}},
            "required": ["q"],
        }}]
    })

    changes = diff_contracts(before, after)
    assert not is_breaking(changes)
    assert overall_severity(changes) == "info"


def test_description_only_change_is_informational():
    before = normalize_mcp({
        "tools": [{"name": "search", "description": "old desc",
                   "inputSchema": {"properties": {}, "required": []}}]
    })
    after = normalize_mcp({
        "tools": [{"name": "search", "description": "new desc",
                   "inputSchema": {"properties": {}, "required": []}}]
    })

    changes = diff_contracts(before, after)
    assert not is_breaking(changes)
    assert changes[0]["type"] == "description_changed"


def test_optional_becomes_required_is_critical():
    before = normalize_mcp({
        "tools": [{"name": "t", "inputSchema": {"properties": {"x": {"type": "string"}}, "required": []}}]
    })
    after = normalize_mcp({
        "tools": [{"name": "t", "inputSchema": {"properties": {"x": {"type": "string"}}, "required": ["x"]}}]
    })

    changes = diff_contracts(before, after)
    assert is_breaking(changes)
    assert any(c["type"] == "optional_to_required" for c in changes)


def test_identical_contracts_produce_no_changes():
    spec = normalize_openapi({
        "paths": {"/ping": {"get": {"parameters": []}}}
    })
    changes = diff_contracts(spec, spec)
    assert changes == []
