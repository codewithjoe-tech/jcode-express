"""
Express.js edge plugin for jcode.

Detects two patterns in JavaScript/TypeScript files:

1. Route registrations — app.get/post/put/delete/patch/all(path, ...handlers)
   → ROUTE edge: caller → final route handler function

2. Middleware mounting — app.use(middleware) / app.use(path, middleware)
   → MIDDLEWARE edge: caller → middleware function

The receiver must look like an Express app or router to avoid false positives
from other objects that happen to have .get() or .use() methods.
Common receiver names matched: app, router, api, server, and any variable
ending in "router", "app", or "api".
"""
from jcode.domain.models import Edge, Node, NodeId, NodeType
from jcode.storage.object_store import node_id_for

EDGE_ROUTE      = "route"       # route registration → handler
EDGE_MIDDLEWARE = "middleware"  # middleware mounting → middleware fn

_ROUTE_METHODS      = frozenset({"get", "post", "put", "delete", "patch", "all"})
_MIDDLEWARE_METHODS = frozenset({"use"})

# Variable names that strongly suggest an Express app or router instance
_APP_NAMES = frozenset({"app", "router", "api", "server"})


def _text(ts_node, source: bytes) -> str:
    return source[ts_node.start_byte:ts_node.end_byte].decode("utf-8", errors="replace")


def _provisional(name: str, node_type: NodeType = NodeType.FUNCTION) -> Node:
    ph = Node(
        id=NodeId("0" * 64), node_type=node_type,
        name=name, title=name, file_path="<unresolved>",
        line_start=0, line_end=0,
    )
    return Node(
        id=node_id_for(ph), node_type=node_type,
        name=name, title=name, file_path="<unresolved>",
        line_start=0, line_end=0,
    )


def _is_express_receiver(call_node, source: bytes) -> bool:
    """
    Return True if the call receiver looks like an Express app or router.

    Checks:
    - Direct name match: app, router, api, server
    - Suffix match: myRouter, authRouter, v1Api, expressApp, etc.
    """
    func_expr = call_node.children[0] if call_node.children else None
    if func_expr is None or func_expr.type != "member_expression":
        return False
    obj = func_expr.child_by_field_name("object")
    if obj is None:
        return False
    name = _text(obj, source).lower()
    return (
        name in _APP_NAMES
        or name.endswith("router")
        or name.endswith("app")
        or name.endswith("api")
    )


def _extract_handler(call_node, source: bytes) -> str | None:
    """
    Extract the route handler name from the call arguments.

    For  app.get('/path', auth, getUsers)  returns  'getUsers'.
    For  app.use(logRequests)              returns  'logRequests'.
    Skips string/template literals (route paths) and looks for the last
    identifier argument, which is the final handler.
    Arrow functions and anonymous functions return None (no useful name).
    """
    args = next((c for c in call_node.children if c.type == "arguments"), None)
    if args is None:
        return None

    candidates = [
        c for c in args.children
        if c.type not in (",", "(", ")", "comment", "string", "template_string")
    ]
    for arg in reversed(candidates):
        if arg.type == "identifier":
            return _text(arg, source)
    return None


class ExpressPlugin:
    """Implements the jcode EdgePlugin protocol for Express.js."""

    @property
    def handled_names(self) -> frozenset:
        return _ROUTE_METHODS | _MIDDLEWARE_METHODS

    def handle_call(self, call_node, source: bytes, caller: Node):
        """
        Intercepts app.get/post/put/delete/patch/all/use calls and emits
        ROUTE or MIDDLEWARE edges to the handler function.
        """
        if not _is_express_receiver(call_node, source):
            return [], []

        func_expr = call_node.children[0]
        prop = func_expr.child_by_field_name("property")
        if prop is None:
            return [], []
        method = _text(prop, source)

        handler_name = _extract_handler(call_node, source)
        if not handler_name:
            return [], []

        edge_type = EDGE_ROUTE if method in _ROUTE_METHODS else EDGE_MIDDLEWARE
        prov = _provisional(handler_name)
        return [prov], [Edge(
            source_id=caller.id,
            target_id=prov.id,
            edge_type=edge_type,
        )]


def create() -> ExpressPlugin:
    return ExpressPlugin()
