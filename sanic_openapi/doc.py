from collections import defaultdict
from datetime import date, datetime


class Field:
    def __init__(self, description=None, required=None, name=None, default=None, enum=None, indata=None):
        self.name = name
        self.description = description
        self.required = required
        self.default = default
        self.enum = enum
        self.indata = indata

    def serialize(self):
        output = {}
        if self.name:
            output['name'] = self.name
        if self.description:
            output['description'] = self.description
        if self.required is not None:
            output['required'] = self.required
        if self.default is not None:
            output['default'] = self.default
        if self.enum is not None:
            output['enum'] = self.enum
        if self.indata is not None:
            output['in'] = self.indata
        return output


class Integer(Field):
    def __init__(self, description=None, required=None, name=None, default=None, enum=None, minimum=None, maximum=None):
        super().__init__(description, required, name, default)
        self.minimum = minimum
        self.maximum = maximum
        
    def serialize(self):
        addition = {}
        if self.minimum is not None:
            addition["minimum"] = self.minimum
        if self.maximum is not None:
            addition["maximum"] = self.maximum
        return {
            "type": "integer",
            "format": "int64",
            **addition,
            **super().serialize()
        }

class File(Field):
    def serialize(self):
        return {
            "type": "file",
            **super().serialize()
        }

class String(Field):
    def serialize(self):
        return {
            "type": "string",
            **super().serialize()
        }

class Float(Field):
    def __init__(self, description=None, required=None, name=None, default=None, enum=None, minimum=None, maximum=None):
        super().__init__(description, required, name, default)
        self.minimum = minimum
        self.maximum = maximum
        
    def serialize(self):
        addition = {}
        if self.minimum is not None:
            addition["minimum"] = self.minimum
        if self.maximum is not None:
            addition["maximum"] = self.maximum
        return {
            "type": "number",
            "format": "float",
            **addition,
            **super().serialize()
        }

class Boolean(Field):
    def serialize(self):
        return {
            "type": "boolean",
            **super().serialize()
        }


class Tuple(Field):
    pass


class Date(Field):
    def serialize(self):
        return {
            "type": "date",
            **super().serialize()
        }


class DateTime(Field):
    def serialize(self):
        return {
            "type": "dateTime",
            **super().serialize()
        }


class Dictionary(Field):
    def __init__(self, fields=None, **kwargs):
        self.fields = fields or {}
        super().__init__(**kwargs)

    def serialize(self):
        return {
            "type": "object",
            "properties": {key: serialize_schema(schema) for key, schema in self.fields.items()},
            **super().serialize()
        }


class List(Field):
    def __init__(self, items=None, *args, **kwargs):
        self.items = items or []
        if type(self.items) is not list:
            self.items = [self.items]
        super().__init__(*args, **kwargs)

    def serialize(self):
        if len(self.items) > 1:
            items = Tuple(self.items).serialize()
        elif self.items:
            items = serialize_schema(self.items[0])
        return {
            "type": "array",
            "items": items
        }


definitions = {}


class Object(Field):
    def __init__(self, cls, *args, object_name=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.cls = cls
        self.object_name = object_name or cls.__name__

        if self.cls not in definitions:
            definitions[self.cls] = (self, self.definition)

    @property
    def definition(self):
        return {
            "type": "object",
            "properties": {
                key: serialize_schema(schema)
                for key, schema in self.cls.__dict__.items()
                if not key.startswith("_")
                },
            **super().serialize()
        }

    def serialize(self):
        return {
            # "type": "object",
            #"schema": {
            "$ref": "#/definitions/{}".format(self.object_name),
            #},
            **super().serialize()
        }


def serialize_schema(schema):
    schema_type = type(schema)

    # --------------------------------------------------------------- #
    # Class
    # --------------------------------------------------------------- #
    if schema_type is type:
        if issubclass(schema, Field):
            return schema().serialize()
        elif schema is dict:
            return Dictionary().serialize()
        elif schema is list:
            return List().serialize()
        elif schema is int:
            return Integer().serialize()
        elif schema is str:
            return String().serialize()
        elif schema is bool:
            return Boolean().serialize()
        elif schema is float:
            return Float().serialize()
        elif schema is date:
            return Date().serialize()
        elif schema is datetime:
            return DateTime().serialize()
        else:
            return Object(schema).serialize()

    # --------------------------------------------------------------- #
    # Object
    # --------------------------------------------------------------- #
    else:
        if issubclass(schema_type, Field):
            return schema.serialize()
        elif schema_type is dict:
            return Dictionary(schema).serialize()
        elif schema_type is list:
            return List(schema).serialize()

    return {}


# --------------------------------------------------------------- #
# Route Documenters
# --------------------------------------------------------------- #


class RouteSpec:
    consumes = None
    consumes_content_type = None
    produces = None
    produces_content_type = None
    summary = None
    description = None
    operation = None
    blueprint = None
    tags = None
    hide = None
    produces_description = None
    produces_examples = None
    headers = None

    def __init__(self):
        self.tags = []
        super().__init__()


route_specs = defaultdict(RouteSpec)


def route(summary=None, description=None, consumes=None, produces=None,
          consumes_content_type=None, produces_content_type=None, hide=None, headers=None):
    def inner(func):
        route_spec = route_specs[func]

        if summary is not None:
            route_spec.summary = summary
        if description is not None:
            route_spec.description = description
        if consumes is not None:
            route_spec.consumes = consumes
        if produces is not None:
            route_spec.produces = produces
        if consumes_content_type is not None:
            route_spec.consumes_content_type = consumes_content_type
        if produces_content_type is not None:
            route_spec.produces_content_type = produces_content_type
        if hide is not None:
            route_spec.hide = hide
        if headers is not None:
            route_spec.headers = headers

        return func
    return inner


def summary(text):
    def inner(func):
        route_specs[func].summary = text
        return func
    return inner


def description(text):
    def inner(func):
        route_specs[func].description = text
        return func
    return inner


def consumes(*args, content_type=None):
    def inner(func):
        if args:
            route_specs[func].consumes = args[0] if len(args) == 1 else args
            route_specs[func].consumes_content_type = content_type
        return func
    return inner


def produces(*args, description='', content_type=None, examples=None):
    def inner(func):
        if args:
            route_specs[func].produces = args[0] if len(args) == 1 else args
            route_specs[func].produces_content_type = content_type
            route_specs[func].produces_description = description
            route_specs[func].produces_examples = examples
        return func
    return inner


def tag(name):
    def inner(func):
        route_specs[func].tags.append(name)
        return func
    return inner

def hide():
    def inner(func):
        route_specs[func].hide = True
        return func
    return inner

def headers(*args):
    def inner(func):
        if args:
            route_specs[func].headers = args[0] if len(args) == 1 else args
        return func
    return inner
