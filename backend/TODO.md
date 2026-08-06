# TODO

- [ ] Fix 500 on POST /auth/register: `relation "users" does not exist`
- [x] Identify root cause: DB schema auto-create is disabled (`DB_AUTO_CREATE=False`) so `init_db()` never runs.
- [ ] Enable DB auto-create in development by changing `DB_AUTO_CREATE` default in `backend/app/core/config.py`
- [ ] Restart backend server
- [ ] Re-test `POST /auth/register` to confirm tables exist and registration succeeds
