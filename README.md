# envault

> A CLI tool for securely managing and injecting environment variables across local and CI environments.

---

## Installation

```bash
pip install envault
```

Or with [pipx](https://pypa.github.io/pipx/) (recommended for CLI tools):

```bash
pipx install envault
```

---

## Usage

Initialize a new vault in your project:

```bash
envault init
```

Add a secret:

```bash
envault set DATABASE_URL "postgres://user:pass@localhost/mydb"
```

Inject variables into a command:

```bash
envault run -- python manage.py runserver
```

Export variables to a `.env` file:

```bash
envault export > .env
```

Secrets are encrypted at rest and can be committed safely to version control. In CI environments, set the `ENVAULT_KEY` environment variable to decrypt and inject secrets automatically.

---

## CI Integration

```yaml
# GitHub Actions example
- name: Run with envault
  env:
    ENVAULT_KEY: ${{ secrets.ENVAULT_KEY }}
  run: envault run -- your-build-command
```

---

## License

[MIT](LICENSE)