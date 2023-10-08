'''
QueryKnot: a lightweight data format for tying LLM queries together with application logic.

JSON, YAML, TOML, etc are ubiquitous. However, having LLMs produce these formats is slow, and consumes a lot of tokens. 
Models that produce JSON require additional training, and currently cost more to run. Not all LLMs can easily produce JSON.

The goal of QueryKnot is to provide a lightweight format that is easy to parse, and easy to produce.

This format can be easily converted other formats, or into objects in a programming language.

QueryKnot is a key-value format that flattens objects into a single level.

Keys are dot separated strings, and values are strings, numbers, booleans, or collections.

Nested collections are not supported. 

Examples: 

user.name "Cansu"
user.age 25
user.location "Istanbul"
conversation.topics ["politics" "sports" "technology"]

'''

from parsy import (
    generate, 
    regex, 
    string, 
    whitespace
)


def trim_whitespace(parser):
    ''' Trim whitespace from the start and end of a parser. '''
    return whitespace.many() >> parser << whitespace.many()
  

class DataTypes:
    ''' A collection of parsers for the data types used in Yarn Spinner. '''
    
    @staticmethod
    @generate
    def string_literal():
        ''' Parse a double quote, then any characters until another double quote. Backslash escapes are supported. '''
        escape = string('\\') >> regex('.')
        expect = regex(r'[^"\\]')
        quotes = trim_whitespace(string('"'))
        content = yield quotes >> (escape | expect).many().concat() << quotes
        return content
    
    @staticmethod
    @generate
    def number():
        ''' Parse a number and convert it to a float. 
            Allows for scientific notation. Example: 6.62607015e-34
        '''
        return (yield trim_whitespace(regex(r'-?\d+(\.\d+)?(e-?\d+)?')).map(float))
    
    @staticmethod
    @generate
    def boolean():
        ''' Parse a boolean string (true or false) and convert it to a bool. '''
        return (
            yield trim_whitespace(
                string('true',  transform=str.lower).result(True) | 
                string('false', transform=str.lower).result(False)
            )
        )
    
    @staticmethod
    @generate
    def key():
        ''' Allows dot separated keys such as a.b.c 
            characters are alphanumeric and underscore
        '''
        return (yield trim_whitespace(regex(r'[a-zA-Z0-9_]*(\.[a-zA-Z0-9_]*)*')))


    @staticmethod
    @generate
    def collection():
        ''' A whitespace separated collection of primative types: strings, numbers, booleans. surrounded by square brackets.
            ChatGPT LOVES adding commas to collections, so they're lowkey supported. 
        '''
        # Whitespace or comma separated values, NOT mixed.
        ws_or_comma = trim_whitespace(string(',') | string(' ').many())
        return (
            yield trim_whitespace(
                string('[') >> (DataTypes.string_literal | DataTypes.number | DataTypes.boolean).sep_by(ws_or_comma) << string(']')
            )  
        )
    
class DataTypesV2(DataTypes):
    ''' Parsers used for V2 of the format.
    '''
            
    @staticmethod
    @generate
    def enum():
        ''' Allows fixed options to be specificed. Options use same rules as key and are separated by pipes.
            Examples: 
                background.colors red|green|blue
                background.colors red | green | blue
                settings.themes light.sunrise|light.sunset|dark
        '''
        

        return (yield trim_whitespace(DataTypesV2.key).sep_by(string('|')))


class Object: 
    def __init__(self, **kwargs) -> None:
        for (key, val) in kwargs.items():
            setattr(self, key, val)
    
    def __eq__(self, o: object) -> bool:
        return self.__dict__ == o.__dict__

    def __repr__(self):
        return f'{self.__dict__}'
    
class Parser:

    def __init__(self):
        self.parsed = None

    @staticmethod
    @generate
    def datum():
        key = yield trim_whitespace(DataTypes.key)
        val = yield trim_whitespace(DataTypes.string_literal | DataTypes.number | DataTypes.boolean | DataTypes.collection)
        return (key, val)

    @staticmethod
    @generate
    def _parser():
        ''' Parse multiple lines of key-value pairs. '''
        return (yield Parser.datum.many())


    def parse(self, input_str):
        self.parsed = self._parser.parse(input_str)
        return self.parsed
    


    def into_dict(self, pairs):
        ''' Convert a list of key-value pairs into a dictionary. 
            Keys are split on dots, and nested dictionaries are created.
            Example in: 
                [('user.name', 'Cansu'), ('user.age', 25), ('user.location', 'Istanbul')]
            Example out: 
                {'user': {'name': 'Cansu', 'age': 25, 'location': 'Istanbul'}}
        '''
        result = {}
        for (key, val) in pairs:
            segments = key.split('.')
            finalseg = segments.pop()
            current = result

            for k in segments:
                current = current.setdefault(k, {})
            current[finalseg] = val
        return result
    


    def into_object(self, dict_data):
        ''' Produce an object from either a dictionary or a list of key-value pairs. 
        '''
        if isinstance(dict_data, list):
            dict_data = self.into_dict(dict_data)
        return self._objectify(dict_data)


    def _objectify(self, data):
        ''' For each key in a dictionary, create an attribute on an object. 
            Example In:
                {'user': {'name': 'Cansu', 'age': 25, 'location': 'Istanbul', 'interests': {'esports': ['Overwatch', 'League of Legends', 'Valorant']}}}
            Example Out:
                <object>
                    user: <object>
                        name: 'Cansu'
                        age: 25
                        location: 'Istanbul'
                        interests: <object>
                            esports: ['Overwatch', 'League of Legends', 'Valorant']

            Calling: into_object(d).user.interests.esports will return ['Overwatch', 'League of Legends', 'Valorant']
        '''
        if isinstance(data, dict):
            obj = Object()
            for (key, val) in data.items():
                setattr(obj, key, self._objectify(val))
            return obj
        elif isinstance(data, list):
            return [self._objectify(item) for item in data]
        else:
            return data


class ParserV2(Parser): ...

def parse_into_object(input_str):
    parser = Parser()
    return parser.into_object(parser.parse(input_str))

def parse_into_dict(input_str):
    parser = Parser()
    return parser.into_dict(parser.parse(input_str))
    

def formatting_instructions():
    return '''
        Output Formatting Instructions:
            Output is formatted using a custom lightweight data format called QueryKnot.
            QueryKnot flattens objects into key-value pairs.

        - Key Format: Keys are dot separated strings containing alphanumeric characters and underscores.
            - Examples: user.name user.age user.is_premium_member hobbies topics settings.theme

        - Value Data Types:
            - String: Enclosed in double quotes. Backslash escapes are supported.
                - Examples: "hello" "hello \"world\""

            - Number: Integer, float, scientific notation; positive or negative.
                - Examples: 1 -10.5 2e-3

            - Boolean: 
                - Examples: true false

            - Collection: Space separated strings numbers booleans contained in square brackets. No nested collections.
                - Examples: [1 2 3] ["a" "b"] [true 1 "a"]
        
        Key are separated from values by a single space. Key-value pairs are separated by a newline.

        Example QueryKnot Output:
            user.name "John Doe"
            user.age 25
            user.is_premium_member true
            hobbies ["coding" "reading" "swimming"]
            topics ["politics" "sports" "technology"]
            settings.theme "dark"

    '''


# Tests for the command parser using unittest
import unittest

class TestDataTypes(unittest.TestCase):

    def _test_parser(self, parser, test_cases, fail_cases=[]):
        for input_str, expected in test_cases:
            with self.subTest(input=input_str, expected=expected):
                self.assertEqual(parser.parse(input_str), expected)
        for input_str in fail_cases:
            with self.subTest(input=input_str):
                with self.assertRaises(Exception):
                    parser.parse(input_str)


    def test_key(self):
        self._test_parser(
            DataTypes.key,
            [
                ('a',           'a'),
                ('a.b',         'a.b'),
                ('a.b.c',       'a.b.c'),
                (' a.b.c.d ',   'a.b.c.d'),
                ('1.0.1.1',     '1.0.1.1'),
                ('_.a.b',       '_.a.b'),
            ]
        )


    def test_collection(self):
        self._test_parser(
            DataTypes.collection,
            [
                ('[1 2 3]',             [1, 2, 3]),
                ('["a" "b" "c"]',       ['a', 'b', 'c']),
                ('[true false true]',   [True, False, True]),
                ('[1 "a" true]',        [1, 'a', True]),
                ('[1, 2, 3]',             [1, 2, 3]),
                ('["a", "b", "c"]',       ['a', 'b', 'c']),
                ('[true, false, true]',   [True, False, True]),
                ('[1, "a", true]',        [1, 'a', True]),
                ('[]',                  [])
                
            ],
            fail_cases=['[1 2 3', '[1 2 text]', '[1 2 [1 2]]']
        )

class TestParser(unittest.TestCase):
    
    def _test_parser(self, parser, test_cases, fail_cases=[]):
        for input_str, expected in test_cases:
            with self.subTest(input=input_str, expected=expected):
                self.assertEqual(parser.parse(input_str), expected)
        for input_str in fail_cases:
            with self.subTest(input=input_str):
                with self.assertRaises(Exception):
                    parser.parse(input_str)


    def test_datum(self):
        self._test_parser(
            Parser.datum,
            [
                ('a 1',                         ('a', 1)),
                ('a.b 1',                       ('a.b', 1)),
                ('a.b.c 1',                     ('a.b.c', 1)),
                ('a.b.c 1.0',                   ('a.b.c', 1.0)),
                ('a.b.c true',                  ('a.b.c', True)),
                ('a.b.c [1 2 3]',               ('a.b.c', [1, 2, 3])),
                ('a.b.c ["a" "b" "c"]',         ('a.b.c', ['a', 'b', 'c'])),
                ('a.b.c [true false true]',     ('a.b.c', [True, False, True])),
                ('a.b.c [1 "a" true]',          ('a.b.c', [1, 'a', True])),
                ('a.b.c []',                    ('a.b.c', [])),
                ('quantum.planck_constant 6.62607015e-34', ('quantum.planck_constant', 6.62607015e-34)),
            ],
             fail_cases=['a.b.c', 'a.b.c 1 2', 'a.b.c test']
        )
        

    def test_parser(self):
        self._test_parser(
            Parser._parser,
            [
                ('a 1',                             [('a', 1)]),
                ('a.b 1',                           [('a.b', 1)]),
                ('a.b.c 1',                         [('a.b.c', 1)]),
                ('a.b.c 1.0',                       [('a.b.c', 1.0)]),
                ('a.b.c true',                      [('a.b.c', True)]),
                ('a.b.c [1 2 3]',                   [('a.b.c', [1, 2, 3])]),
                ('a.b.c ["a" "b" "c"]',             [('a.b.c', ['a', 'b', 'c'])]),
                ('a.b.c [true false true]',         [('a.b.c', [True, False, True])]),
                ('a.b.c [1 "a" true]',              [('a.b.c', [1, 'a', True])]),
                ('a.b.c []',                        [('a.b.c', [])]),
                ('a 1\nb 2',                        [('a', 1), ('b', 2)]),
                ('a 1\nb 2\nc 3',                   [('a', 1), ('b', 2), ('c', 3)]),
                ('a 1\nb 2\nc 3\nd 4',              [('a', 1), ('b', 2), ('c', 3), ('d', 4)]),
                ('a 1\nb 2\nc 3\nd 4\ne 5',         [('a', 1), ('b', 2), ('c', 3), ('d', 4), ('e', 5)]),
                ('''user.name "Cansu"
                    user.age 25
                    user.location "Istanbul"
                 ''',                               [('user.name', 'Cansu'), ('user.age', 25), ('user.location', 'Istanbul')]
                )
            ],
            fail_cases=['a.b.c', 'a.b.c 1 2', 'a.b.c test']
        )
 

    def test_into_dict(self):
        test_cases = [
            ([('a', 1)],        {'a': 1}),
            ([('a.b', 1)],      {'a': {'b': 1}}),
            ([('a.b.c', 1)],    {'a': {'b': {'c': 1}}}),
            ([('a.b.c', 1.0)],  {'a': {'b': {'c': 1.0}}}),
            ([('a.b.c', True)],                 {'a': {'b': {'c': True}}}),
            ([('a.b.c', [1, 2, 3])],            {'a': {'b': {'c': [1, 2, 3]}}}),
            ([('a.b.c', ['a', 'b', 'c'])],      {'a': {'b': {'c': ['a', 'b', 'c']}}}),
            ([('a.b.c', [True, False, True])],  {'a': {'b': {'c': [True, False, True]}}}),
            ([('a.b.c', [1, 'a', True])],       {'a': {'b': {'c': [1, 'a', True]}}}),
            ([('a.b.c', [])],                   {'a': {'b': {'c': []}}}),
            ([('a', 1), ('b', 2)],              {'a': 1, 'b': 2}),
            ([('a', 1), ('b', 2), ('c', 3)],    {'a': 1, 'b': 2, 'c': 3}),
            ([('a', 1), ('b', 2), ('c', 3), ('d', 4)],              {'a': 1, 'b': 2, 'c': 3, 'd': 4}),
            ([('a', 1), ('b', 2), ('c', 3), ('d', 4), ('e', 5)],    {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5}),
            ([('user.name', 'Cansu'), ('user.age', 25), ('user.location', 'Istanbul')], {
                'user': {
                    'name': 'Cansu',
                    'age': 25,
                    'location': 'Istanbul'
                }
            }),
        ]
        parser = Parser()
        for (actual, expect) in test_cases:
            with self.subTest(input=actual, expected=expect):
                assert parser.into_dict(actual) == expect, parser.into_dict(actual)


    def test_into_object(self):
        class Object: 
            def __init__(self, **kwargs) -> None:
                for (key, val) in kwargs.items():
                    setattr(self, key, val)
            
            def __eq__(self, o: object) -> bool:
                return self.__dict__ == o.__dict__

            def __repr__(self):
                return f'{self.__dict__}'
            
        data = [
            ('a.b', 1),
            ('user.name', 'Cansu'),
            ('user.age', 25),
            ('user.location', 'Istanbul')
        ]
        expected = Object(
            a = Object(
                b = 1
            ),
            user = Object(
                name = 'Cansu',
                age = 25,
                location = 'Istanbul'
            )
        )

        parser = Parser()
        assert parser.into_object(parser.into_dict(data)) == expected
        assert parser.into_object(data) == expected



class TestDataTypesV2(unittest.TestCase):
    def _test_parser(self, parser, test_cases, fail_cases=[]):
        for input_str, expected in test_cases:
            with self.subTest(input=input_str, expected=expected):
                self.assertEqual(parser.parse(input_str), expected)
        for input_str in fail_cases:
            with self.subTest(input=input_str):
                with self.assertRaises(Exception):
                    parser.parse(input_str)


    def test_enum(self):
        self._test_parser(
            DataTypesV2.enum,
            [
                ('a|b|c',             ['a', 'b', 'c']),
                ('a.b|c.d|e.f',       ['a.b', 'c.d', 'e.f']),
                ('a.b.c|d.e.f|g.h.i', ['a.b.c', 'd.e.f', 'g.h.i']),
            ]
        )


# Run the tests
if __name__ == '__main__':
    unittest.main(verbosity=2, exit=False)
    