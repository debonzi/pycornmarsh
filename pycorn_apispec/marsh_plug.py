from apispec.ext import marshmallow
from apispec.ext.marshmallow import common
from marshmallow_oneofschema import OneOfSchema


class OneofOpenAPIConverter(marshmallow.OpenAPIConverter):
    def schema2jsonschema(self, schema):
        if self.openapi_version.major < 3 or not is_oneof(schema):
            return super(OneofOpenAPIConverter, self).schema2jsonschema(schema)
        mapping = {}
        oneof = []
        for name, type_schema in schema.type_schemas.items():
            schema_instance = common.resolve_schema_instance(type_schema)
            schema_key = common.make_schema_key(schema_instance)
            if schema_key not in self.refs:
                component_name = self.schema_name_resolver(type_schema) or name
                self.spec.components.schema(component_name, schema=type_schema)
            ref_dict = self.get_ref_dict(schema_instance)
            mapping.update({name: ref_dict['$ref']})
            oneof.append(ref_dict)

        return {
            'oneOf': oneof,
            'discriminator': {
                'propertyName': schema.type_field,
                'mapping': mapping
            }
        }


def is_oneof(schema):
    return (
            (isinstance(schema, type) and issubclass(schema, OneOfSchema))
            or
            isinstance(schema, OneOfSchema)
    )


class MarshmallowPlugin(marshmallow.MarshmallowPlugin):
    Converter = OneofOpenAPIConverter

    def init_spec(self, spec):
        super(MarshmallowPlugin, self).init_spec(spec)
        self.spec = spec
        self.openapi_version = spec.openapi_version
        self.openapi = OneofOpenAPIConverter(
            openapi_version=spec.openapi_version,
            schema_name_resolver=self.schema_name_resolver,
            spec=spec,
        )
