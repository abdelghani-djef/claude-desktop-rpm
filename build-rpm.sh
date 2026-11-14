#!/usr/bin/env bash
# Build a Fedora RPM from Anthropic's official claude-desktop .deb.
#
#   ./build-rpm.sh                 # download the latest .deb, verify, build
#   ./build-rpm.sh path/to/x.deb   # build from a .deb you already have
#
# Result: ./out/claude-desktop-<version>-1.repack.<dist>.<arch>.rpm
# Install/upgrade with: sudo dnf install ./out/claude-desktop-*.rpm
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="https://downloads.claude.ai/claude-desktop/apt/stable"
TOP="$HERE/rpmbuild"
OUT="$HERE/out"
DEB_DIR="$HERE/deb"

case "$(uname -m)" in
  x86_64)  DEB_ARCH=amd64 ;;
  aarch64) DEB_ARCH=arm64 ;;
  *) echo "Unsupported architecture: $(uname -m)" >&2; exit 1 ;;
esac

command -v rpmbuild >/dev/null || { echo "rpmbuild missing: sudo dnf install rpm-build" >&2; exit 1; }

mkdir -p "$DEB_DIR" "$OUT"

if [[ $# -ge 1 ]]; then
  DEB="$(realpath "$1")"
else
  echo ">> Fetching package index"
  INDEX="$(curl -fsSL "$REPO/dists/stable/main/binary-$DEB_ARCH/Packages")"
  # Pick the newest claude-desktop stanza and read its Filename + SHA256.
  read -r FILE SHA < <(awk '
    /^Package: /  { pkg=$2 }
    /^Version: /  { ver=$2 }
    /^Filename: / { file=$2 }
    /^SHA256: /   { sha=$2 }
    /^$/ { if (pkg=="claude-desktop" && file!="") print ver, file, sha; pkg=file=sha="" }
    END  { if (pkg=="claude-desktop" && file!="") print ver, file, sha }
  ' <<<"$INDEX" | sort -V -k1,1 | tail -n1 | cut -d' ' -f2-)
  [[ -n "${FILE:-}" ]] || { echo "No claude-desktop package found in index" >&2; exit 1; }
  DEB="$DEB_DIR/$(basename "$FILE")"
  if [[ ! -f "$DEB" ]] || ! echo "$SHA  $DEB" | sha256sum -c --status; then
    echo ">> Downloading $(basename "$FILE")"
    curl -fL --progress-bar -o "$DEB.part" "$REPO/$FILE"
    mv "$DEB.part" "$DEB"
  fi
  echo "$SHA  $DEB" | sha256sum -c --quiet || { echo "SHA256 mismatch — aborting" >&2; exit 1; }
  echo ">> SHA256 verified"
fi

# Version from the .deb's own control file.
VERSION="$(ar p "$DEB" control.tar.xz | tar -xJO ./control | awk '/^Version:/ {print $2}')"
[[ -n "$VERSION" ]] || { echo "Could not read version from $DEB" >&2; exit 1; }
echo ">> claude-desktop $VERSION ($DEB_ARCH)"

rm -rf "$TOP"
mkdir -p "$TOP"/{SOURCES,SPECS,BUILD,RPMS,SRPMS}
cp "$DEB" "$TOP/SOURCES/claude-desktop_${VERSION}_${DEB_ARCH}.deb"
cp "$HERE/claude-desktop.spec" "$TOP/SPECS/"

rpmbuild -bb \
  --define "_topdir $TOP" \
  --define "deb_version $VERSION" \
  "$TOP/SPECS/claude-desktop.spec"

find "$TOP/RPMS" -name '*.rpm' -exec mv -f {} "$OUT/" \;
rm -rf "$TOP"
echo
echo ">> Built:"
ls -lh "$OUT"/claude-desktop-"$VERSION"-*.rpm
echo
echo "Install with:  sudo dnf install $OUT/claude-desktop-$VERSION-*.rpm"
