# Repackages Anthropic's official claude-desktop .deb as an RPM for Fedora.
# Personal use only — do not redistribute the resulting RPM.
#
# Build with ./build-rpm.sh, which supplies the deb_version macro and the .deb.

%{!?deb_version: %global deb_version 0}

# Prebuilt Electron binaries: no debuginfo, no stripping, no brp mangling.
%global debug_package %{nil}
%global __os_install_post %{nil}
%define _build_id_links none

%ifarch x86_64
%global deb_arch amd64
%endif
%ifarch aarch64
%global deb_arch arm64
%endif

Name:           claude-desktop
Version:        %{deb_version}
Release:        1.repack%{?dist}
Summary:        Desktop application for Claude.ai
License:        Proprietary
URL:            https://claude.ai
Source0:        claude-desktop_%{version}_%{deb_arch}.deb

ExclusiveArch:  x86_64 aarch64
BuildRequires:  binutils
BuildRequires:  tar
BuildRequires:  xz

# The bundled Electron libs must not leak into RPM's provides/requires.
AutoReqProv:    no

# Fedora equivalents of the .deb Depends:
Requires:       gtk3
Requires:       libnotify
Requires:       nss
Requires:       xdg-utils
Requires:       at-spi2-core
Requires:       libdrm
Requires:       mesa-libgbm
Requires:       libxcb
Requires:       libsecret
Requires:       glibc >= 2.34
Requires:       libXtst
Requires:       libuuid
Requires:       pipewire-libs
Requires:       glib2
Requires:       xdg-desktop-portal
Requires:       (xdg-desktop-portal-gtk or xdg-desktop-portal-gnome or xdg-desktop-portal-kde)

# Fedora equivalents of the .deb Recommends: (installed by default by dnf)
Recommends:     alsa-lib
Recommends:     libayatana-appindicator-gtk3
Recommends:     ca-certificates
Recommends:     (gnome-keyring or kf6-kwallet)
Recommends:     bubblewrap
Recommends:     socat
Recommends:     openssh-clients
# Cowork VM support (QEMU/KVM + UEFI + virtiofs)
%ifarch x86_64
Recommends:     qemu-system-x86-core
Recommends:     edk2-ovmf
%endif
%ifarch aarch64
Recommends:     qemu-system-aarch64-core
Recommends:     edk2-aarch64
%endif
Recommends:     virtiofsd

%description
Anthropic's Claude desktop app (Chat, Cowork and Claude Code), repackaged
from the official Debian package for Fedora. Updates are not automatic:
rebuild from a newer .deb to upgrade.

%prep
%setup -q -c -T
ar x %{SOURCE0} data.tar.xz
tar -xJf data.tar.xz
rm -f data.tar.xz
# Debian-only metadata
rm -rf usr/share/lintian

%build
# Nothing to build: prebuilt binaries.

%install
cp -a usr %{buildroot}/

# Electron's SUID sandbox helper (fallback if user namespaces are unavailable).
# Files are owned by root via the default %%defattr; the mode is kept as-is.
chmod 4755 %{buildroot}%{_prefix}/lib/claude-desktop/chrome-sandbox

# What the .deb postinst copies into place at install time — owned by the
# package here instead, so no scriptlets are needed. Fedora's file triggers
# (shared-mime-info, hicolor-icon-theme, desktop-file-utils) refresh caches.
res=%{buildroot}%{_prefix}/lib/claude-desktop/resources
install -Dpm0644 $res/gnome-search-provider/com.anthropic.Claude.search-provider.ini \
    %{buildroot}%{_datadir}/gnome-shell/search-providers/com.anthropic.Claude.search-provider.ini
install -Dpm0644 $res/gnome-search-provider/com.anthropic.Claude.SearchProvider.service \
    %{buildroot}%{_datadir}/dbus-1/services/com.anthropic.Claude.SearchProvider.service
install -Dpm0644 $res/linux-mime/com.anthropic.Claude.xml \
    %{buildroot}%{_datadir}/mime/packages/com.anthropic.Claude.xml

# `ccd` terminal launcher, only when this build ships one (mirrors postinst).
if [ -x $res/bin/ccd ]; then
    ln -s ../lib/claude-desktop/resources/bin/ccd %{buildroot}%{_bindir}/ccd
fi

# Generate the file list so the optional ccd link is handled automatically.
echo %{_bindir}/claude-desktop > %{_builddir}/bin-files.list
[ -L %{buildroot}%{_bindir}/ccd ] && echo %{_bindir}/ccd >> %{_builddir}/bin-files.list
true

%files -f %{_builddir}/bin-files.list
%dir %{_prefix}/lib/claude-desktop
%{_prefix}/lib/claude-desktop/*
%{_datadir}/applications/com.anthropic.Claude.desktop
%{_datadir}/icons/hicolor/*/apps/claude-desktop.png
%{_datadir}/gnome-shell/search-providers/com.anthropic.Claude.search-provider.ini
%{_datadir}/dbus-1/services/com.anthropic.Claude.SearchProvider.service
%{_datadir}/mime/packages/com.anthropic.Claude.xml
%doc %{_docdir}/claude-desktop

%changelog
* Sat Nov 14 2026 Local Repack <root@localhost> - %{deb_version}-1.repack
- Repackaged from the official claude-desktop .deb
