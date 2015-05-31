import sys
if sys.version_info < (3,):
    range = xrange

class Indexer:
    """Indexes CSS property and statement definitions.

    >>> idx = Indexer()
    >>> idx.index(definitions)

    >>> idx.properties.get("pad")
    ("padding", { "unit": "px" })

    >>> idx.full_properties.get("padding")
    ("padding", { "unit": "px" })

    >>> idx.statements.get("m0a")
    ("margin", "0 auto", {})
    """
    def __init__(self):
        self.properties = {} # indexed by shorthand ("bg")
        self.statements = {} # indexed by shorthand ("m0a")
        self.full_properties = {} # indexed by long property name ("margin")

    def index(self, defs):
        """Adds definitions to the index.

        >>> idx.index({ "properties": [...], "definitions": [...] })
        """
        for (short, prop, options) in defs["properties"]:
            options["canonical"] = short
            update_aliases(short, prop, options)

            self.properties[short] = (prop, options)
            self.full_properties[prop] = options

        for (short, prop, value, options) in defs["statements"]:
            options["canonical"] = short
            update_aliases(short, None, options)
            self.statements[short] = (prop, value, options)

        for (short, prop, options) in defs["properties"]:
            apply_fuzzies(self.properties, short, prop, options)

        for (short, prop, value, options) in defs["statements"]:
            apply_fuzzies(self.statements, short, prop, options)

        self.remove_tags()

    def remove_tags(self):
        """Workaround to stop tags from being expanded. This will allow you to type
        `li:before` without `li:` being expanded to `line-height:`.
        
        This is also important for indented syntaxes, where you might commonly
        type `p` on its own line (in contrast to `p {`).
        """
        tags = ['a', 'p', 'br', 'b', 'i', 'li', 'ul', 'div', 'em', 'sup', \
                'big', 'small', 'sub']
        for tag in tags:
            self.statements[tag] = None
            self.properties[tag] = None

def apply_fuzzies(properties, short, prop, options):
    """Propagates 'alias' into the `properties` index
    """
    def iterate(property):
        for key in fuzzify(property):
            if not key in properties:
                properties[key] = properties[short]

    if options and "alias" in options:
        [iterate(alias) for alias in options["alias"]]

def fuzzify(str):
    """Returns a generator with fuzzy matches for a given string.

    >>> for s in fuzzify("border"):
    >>>     print s
    "b", "bo", "bor", "bord", "borde"
    """
    if str:
        for i in range(1, len(str)+1):
            yield str[0:i]

def update_aliases(short, prop, options):
    if not "alias" in options:
        options["alias"] = []

    if prop != None:
        # Insert the property itself
        options["alias"].append(prop)

        # If the property has dashes, addd non-dashed versions
        if '-' in prop:
            options["alias"].append(prop.replace('-', ''))

    # Add the short, but only if there's nothing like it
    # TODO deprecate this
    likeit = [a for a in options["alias"] if a[0:len(short)] == short]
    if len(likeit) == 0:
        options["alias"].insert(0, short)
