# Contribution Guide

If you're reading this, you're likely interested in contributing to `django-easy-audit`. Thank you! This project could not continue without contributors like you.

This guide lays the foundational principles and technical documentation for contributing to this project. If you're considering adding to this project, please read this document in its entirety.

### Contributions

If your motivation is centered around a problem you're facing, please create an issue first after a search of the existing issues to ensure you aren't creating a duplicate. Issues are important as they illustrate the need and document the change process in this package.

Documentation contributions are arguably more important than writing code, so if you've found missing documentation or want to expand upon/clarify existing docs to help your fellow users, we welcome your work!

Do note that contributions that clearly fall outside the scope of this project will be declined. Please give careful thought to the nature of your idea before doing any work.

### Responsibilities

- Ensure cross-platform compatibility for every change that's accepted. Windows, Mac, Debian & Ubuntu Linux.
- Ensure that any new code you write is covered by tests.
- Create issues for any changes and enhancements. Discuss things transparently and get community feedback.
- Keep changes as small as possible to ease the burden of code review.
- Be welcoming to newcomers and encourage diverse new contributors from all backgrounds. See the [Python Community Code of Conduct](https://www.python.org/psf/codeofconduct/).

## Your First Contribution

Never contributed to open-source before? Unsure of where to begin contributing to `django-easy-audit`? You can start by looking through these resources:

- [Make a Pull Request](http://makeapullrequest.com/)
- [First Timers Only](http://www.firsttimersonly.com/)
- [How to Contribute to an Open Source Project on GitHub](https://egghead.io/series/how-to-contribute-to-an-open-source-project-on-github)

If you're still unsure, feel free to ask for help! Everyone starts as a beginner.

## Making changes

For something that is bigger than a one or two line fix:

1. Create your own fork of the code.
2. Make the changes in your fork.
3. Create a pull request from your fork against the main branch.

Small contributions such as fixing spelling errors, where the content is small enough to not be considered intellectual property, can be submitted as a patch without forking.

As a rule of thumb, changes are obvious fixes if they do not introduce any new functionality or creative thinking. As long as the change does not affect functionality, some likely examples include the following:

- Spelling / grammar fixes
- Typo correction, white space and formatting changes
- Comment clean up
- Bug fixes that change default return values or error codes stored in constants
- Adding logging messages or debugging output
- Changes to ‘metadata’ files like .gitignore, build scripts, etc.
- Moving source files from one directory or package to another

## Reporting bugs

### Security vulnerabilities

If you find a security vulnerability, **DO NOT** open an issue. Email [natancalzolari@gmail.com](mailto:natancalzolari@gmail.com) instead so as to not expose the vulnerability to the public.

In order to determine whether you are dealing with a security issue, ask yourself these two questions:

- Can I access something that's not mine, or something I shouldn't have access to?
- Can I disable something for other people?

If the answer to either of those two questions are _yes_, then you're probably dealing with a security issue. Note that even if you answer _no_ to both questions, you may still be dealing with a security issue, so if you're unsure just send an email.

### Bugs

When filing an issue, make sure to answer these five questions:

1. What version of Python and Django are you using?
   ```
   python --version
   django-admin --version
   ```
2. What operating system and processor architecture are you using?
3. What did you do?
4. What did you expect to see?
5. What did you see instead?

### Features or enhancements

If you find yourself wishing for a feature that doesn't exist in `django-easy-audit`, you are probably not alone. There are bound to be others out there with similar needs. Many of the features that `django-easy-audit` has today have been added because our users saw the need. Open an issue on our issues list on GitHub which describes the feature you would like to see, why you need it, and how it should work.

## Setting up a development environment

This project uses the following tools.

- [Poetry](https://python-poetry.org/) for management of packaging, dependencies, and virtual environments
- [pytest](https://docs.pytest.org/) for writing tests
- [ruff](https://astral.sh/ruff) for Python source linting and formatting
- [djLint](https://www.djlint.com/) for HTML linting and formatting
- [pre-commit](https://pre-commit.com/) for Git hooks

### Installing dependencies

1. Install Python. You should use the lowest version of Python that this project supports to ensure your code changes don't include features that are only available in the latest Python version. This specifier can be found in [pyproject.toml](pyproject.toml) under `tool.poetry.dependencies.python`. The official installers can be found here: [Download Python](https://www.python.org/downloads/)
2. [Install Poetry](https://python-poetry.org/docs/#installing-with-the-official-installer). We recommend you use the official installer:

   ```
   curl -sSL https://install.python-poetry.org | python3 -
   ```

   Verify the installation by running `poetry --version`.

3. Navigate to the repository root and [install this package](https://python-poetry.org/docs/cli/#install) and its dependencies:

   ```
   poetry install
   ```

   This project is configured to create a virtual environment inside the project root (`./.venv`). The following commands may change depending on how you choose to [use the Poetry virtual environment](https://python-poetry.org/docs/basic-usage/#using-your-virtual-environment). The easiest way to do this is to simply run the `poetry shell` command to activate the environment.

4. Install pre-commit into your git hooks:

   ```
   pre-commit install
   ```

### Verifying your setup

To verify that your setup is working, run the following commands:

```
pytest
ruff .
djlint .
pre-commit run --all-files
```

If any of the above processes fail, please reach out to the project maintainers for support!
