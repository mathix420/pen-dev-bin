# pen-dev-bin

Arch Linux packaging for [Pen](https://www.pen.dev/downloads), formerly Pencil.
Uses the official tarball with bundled Electron, with x86_64 and aarch64 support.

## Install

From this checkout:

```sh
makepkg -si
```

From [the AUR](https://aur.archlinux.org/packages/pen-dev-bin):

```sh
yay -S pen-dev-bin
```

Both variants conflict with each other and the old Pencil packages. The package
manager will offer to remove the conflicting package during installation.
The command is `pen-dev`; `pencil-dev` remains available as a compatibility alias.
The desktop entry retains upstream's `pencil:` URL handler for authentication.
User configuration is left to the application to migrate.

The MCP server has a stable path at `/opt/pen-dev/mcp-server`.
Update existing MCP configurations that reference the old package directory.

The bundled `chrome-sandbox` is installed with mode 4755, as required for its
setuid sandbox. No additional sandbox-disabling flags are added.

## Updates and CI

Based on [mathix420/beeper-v4-bin](https://github.com/mathix420/beeper-v4-bin):

- Check upstream every six hours, on manual dispatch, or on a `new-version`
  repository dispatch event.
- Read the latest stable release from `highagency/pen-desktop-releases`.
- Pin versioned release URLs and GitHub's SHA-256 digests for both architectures.
- Fail if either asset is missing, a digest is missing, or the version goes backward.
- Increment `pkgrel` if upstream replaces an asset without changing its version.
- Regenerate `.SRCINFO`, build both architectures in an Arch container, commit the
  update, and synchronize the packaging files to a separate AUR Git history.
- Retry AUR synchronization on every scheduled run, even without a version bump.

The build checks ARM packaging without running ARM executables. CI does not launch
the desktop UI. No application binaries are uploaded to GitHub or the AUR.

Local commands:

```sh
python scripts/update.py
makepkg --printsrcinfo > .SRCINFO
python -m unittest discover -s tests -v
bash scripts/validate.sh  # requires Docker; builds in a fresh Arch container
bash scripts/publish.sh   # requires an SSH key registered with the AUR
```

### Repository setup

Use a GitHub repository with `master` as its default branch. Configure:

- Secret `AUR_SSH_PRIVATE_KEY`: the private key for an AUR account authorized to
  maintain `pen-dev-bin`.
- Variable `AUR_KNOWN_HOSTS`: an AUR SSH host key entry whose fingerprint has been
  verified against [the AUR homepage](https://aur.archlinux.org/).

The auto-update workflow needs permission to write repository contents. First run
it manually after configuring these values. The validation workflow also runs on
pushes and pull requests, without publication credentials.

## Rename of the old package

Publish and verify `pen-dev-bin` first. Then submit an AUR **merge** request from
`pencil-dev-bin` to `pen-dev-bin` using the text in [MIGRATION.md](MIGRATION.md).
An accepted AUR merge transfers votes and comments and removes the old package
listing. A separate deletion request is unnecessary after a successful merge.

The recipes declare `provides` and `conflicts` for the old application. They do
not use `replaces` to force a transition between AUR packages.

## License

Pen is proprietary. `LICENSE` contains the upstream EULA retrieved from
https://www.pen.dev/eula on 2026-09-28. The packaged icon comes from Pen 1.2.14.
The application itself is downloaded directly from upstream during the build.
