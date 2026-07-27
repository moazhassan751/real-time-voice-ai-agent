import pytest
from tools import TOOL_SCHEMAS, TOOL_DISPATCH

def test_schema_dispatch_parity():
    schema_names = {s["function"]["name"] for s in TOOL_SCHEMAS}
    dispatch_names = set(TOOL_DISPATCH.keys())
    
    assert schema_names == dispatch_names, "Mismatch between TOOL_SCHEMAS and TOOL_DISPATCH"

def test_schemas_validity():
    for schema in TOOL_SCHEMAS:
        assert "type" in schema
        assert schema["type"] == "function"
        
        func = schema.get("function", {})
        assert "name" in func, "Schema missing function name"
        assert "description" in func, "Schema missing function description"
        assert "parameters" in func, "Schema missing parameters block"
        
        params = func.get("parameters", {})
        assert params.get("type") == "object", "Parameters must be of type object"
        
        # Check for properties definition if args are expected
        # Assuming if a tool expects args, properties must not be empty
        # If a tool expects no args, properties can be empty
        # We can just check that properties is a dict
        assert isinstance(params.get("properties", {}), dict)
