# claude-desktop-rpm

Build a Fedora RPM of the **Claude desktop app** from Anthropic's official Debian package.

> [!IMPORTANT]
> **Unofficial.** This project is not affiliated with, endorsed by, or supported by Anthropic.
> It contains **no Anthropic code or binaries**. It only contains a build recipe. The script
> downloads the official `.deb` from Anthropic's own repository, verifies it, and repackages it
> on your machine. Don't redistribute the RPMs it produces.
>
> Anthropic [officially supports](https://code.claude.com/docs/en/desktop-linux) Debian and Ubuntu only,
> with Fedora support "coming in the future". Once that ships, use the official package instead.

## Requirements

- Fedora (tested on Fedora 45), x86_64 or aarch64
- `rpm-build`, `curl`, `binutils`, `xz`

```bash
sudo dnf install rpm-build curl binutils xz
```

## Build and install

```bash
git clone https://github.com/abdelghani-djef/claude-desktop-rpm.git
cd claude-desktop-rpm
./build-rpm.sh
sudo dnf install ./out/claude-desktop-*.rpm
```

`build-rpm.sh`:

1. Reads Anthropic's apt index (`downloads.claude.ai/claude-desktop/apt/stable`) and picks the newest package for your architecture
2. Downloads the `.deb` and **verifies its SHA256** against the index
3. Builds `out/claude-desktop-<version>-1.repack.<dist>.<arch>.rpm` with `claude-desktop.spec`

If you already have a `.deb`, pass it directly: `./build-rpm.sh path/to/claude-desktop_X_amd64.deb`.

Launch **Claude** from your app launcher, or run `claude-desktop`.

## Updating

The app doesn't update itself on Linux, and this RPM doesn't add a repository. To update, run
`./build-rpm.sh` again and install the new RPM with `sudo dnf install ./out/claude-desktop-<new-version>-*.rpm`.

## What the RPM does differently from the .deb

| `.deb` postinst step | In this RPM |
|---|---|
| Install AppArmor userns profile | Skipped. Fedora uses SELinux and allows unprivileged user namespaces |
| Add apt repo, signing key and unattended-upgrades config | Skipped. Doesn't apply to dnf |
| Copy GNOME Shell search provider files | Packaged as regular files |
| Register `.mcpb` / `.dxt` / `.skill` MIME types | Packaged as a regular file. Fedora's file triggers refresh the MIME cache |
| Link `/usr/bin/ccd` (when the build ships one) | Same, decided at build time |

Debian dependencies are mapped to Fedora package names. RPM's automatic dependency
detection is turned off so the bundled Electron libraries don't leak into the package metadata.
`chrome-sandbox` is installed setuid root (`4755`), as Electron expects.

## Cowork (optional)

Cowork runs tasks in a QEMU/KVM virtual machine. The RPM pulls in `qemu-system-x86-core`,
`edk2-ovmf` and `virtiofsd` as weak dependencies. You also need:

```bash
sudo usermod -aG kvm $USER          # then log out and back in
sudo modprobe vhost_vsock
echo vhost_vsock | sudo tee /etc/modules-load.d/vhost_vsock.conf
```

## Uninstall

```bash
sudo dnf remove claude-desktop
```

## Why not Flathub?

Flathub doesn't accept third-party packages of broad developer tools like IDEs or terminals.
Claude Desktop's Code tab falls into that category. The Flatpak sandbox would also break its
integrated terminal, host tooling and Cowork VMs. Only Anthropic could reasonably publish it there.

## License

The scripts and spec in this repository are MIT licensed (see [LICENSE](LICENSE)).
The Claude desktop app itself is proprietary software owned by Anthropic PBC. Your use of it is
governed by Anthropic's terms.
