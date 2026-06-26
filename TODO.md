# ootlot — Code Review TODO
> Scope: `flows/` and `texts/` folders · Generated after localization refactor
---

## 🔵 Architecture Note (not a quick task — just write it down)

### The bilingual infrastructure is inert
Both `t(key, lang="en", ...)` and `b(key, lang="en", ...)` always default to `"en"`.
No callsite ever passes a different value. All Arabic translations exist and are correct,
but nothing selects them at runtime. `User` also has no `lang` field.

This is fine for now (YAGNI). When the time comes:
1. Add `User.lang = "en"`
2. Look it up where you call `t()` / `b()`
3. Decide: thread as a parameter, or use a context variable

---
