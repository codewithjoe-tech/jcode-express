# jcode-express

Express.js route and middleware edges for [jcode](https://github.com/codewithjoes-tech/jcode).

## What it does

Detects Express.js route registrations and middleware mounting, emitting typed edges — so blast radius queries show every route affected when you change a handler or middleware function.

| Pattern | Edge emitted |
|---------|-------------|
| `app.get('/path', handler)` / `post` / `put` / `delete` / `patch` | `route`: module → handler function |
| `app.use(middleware)` / `router.use(path, middleware)` | `middleware`: module → middleware function |

## Install

```bash
jcode add express
```

## How it works

Once installed, jcode auto-detects this plugin on any repo that has `express` in its `package.json`. No configuration needed.

```js
// jcode sees this:
app.get('/users', authenticate, getUsers)
app.post('/users', authenticate, createUser)
app.use(requestLogger)

// and emits:
// module --[route]--> getUsers
// module --[route]--> createUser
// module --[middleware]--> requestLogger
```

Works with any receiver that looks like an Express app or router — `app`, `router`, `authRouter`, `v1Api`, etc.

## Part of the jcode ecosystem

- [jcode](https://github.com/codewithjoes-tech/jcode) — core CLI and MCP server
- [jcode-registry](https://github.com/codewithjoes-tech/jcode-registry) — plugin registry

---

Made by [Joel Thomas](https://codewithjoe.in)
