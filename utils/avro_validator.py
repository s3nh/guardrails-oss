import json
from fastavro.schema import parse_schema
from fastavro.schema import SchemaParseException

def validate_with_fastavro(schema_dict):
    try:
        # This validates the schema syntax without needing data
        parsed_schema = parse_schema(schema_dict)
        print("Schema syntax is valid!")
        return True
    except SchemaParseException as e:
        print(f"Invalid schema: {e}")
        return False
    except ValueError as e:
        print(f"Schema validation error: {e}")
        return False

# Example usage
schema_dict = {
    "type": "record",
    "name": "User",
    "fields": [
        {"name": "name", "type": "string"},
        {"name": "age", "type": "int"}
    ]
}

validate_with_fastavro(schema_dict)
