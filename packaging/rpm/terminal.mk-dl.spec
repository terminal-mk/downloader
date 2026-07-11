Name:           terminal.mk-dl
Version:        1.0.0
Release:        1%{?dist}
Summary:        Batch downloader for terminal.mk filing attachments
License:        MIT
URL:            https://github.com/terminal-mk/downloader
BuildArch:      x86_64
Requires:       glibc

# Expects the PyInstaller onefile binary already built at
# %{_sourcedir}/terminal.mk-dl (see build_scripts/build_linux.sh), and
# the icon shipped in this repo at packaging/rpm/icons/terminal.mk-dl.png.
Source0:        terminal.mk-dl
Source1:        terminal.mk-dl.png

%description
Companion app for terminal.mk's CF (Corporate Filings) view. Receives a
batch handed off from the "Download All" button -- either via the
terminalmk-dl:// URL protocol or a fallback CSV -- and downloads every
attachment locally, working around browser popup/CORS limits.

%install
mkdir -p %{buildroot}/usr/bin
install -m 755 %{SOURCE0} %{buildroot}/usr/bin/terminal.mk-dl

mkdir -p %{buildroot}/usr/share/icons/hicolor/256x256/apps
install -m 644 %{SOURCE1} %{buildroot}/usr/share/icons/hicolor/256x256/apps/terminal.mk-dl.png

mkdir -p %{buildroot}/usr/share/applications
cat > %{buildroot}/usr/share/applications/terminal.mk-dl.desktop <<EOF
[Desktop Entry]
Type=Application
Name=Terminal MK - Downloader
Comment=Batch-downloads filing attachments handed off from terminal.mk
Exec=/usr/bin/terminal.mk-dl open %u
Terminal=false
NoDisplay=true
Categories=Network;FileTransfer;Utility;
StartupNotify=false
Icon=terminal.mk-dl
MimeType=x-scheme-handler/terminalmk-dl;
EOF

%files
/usr/bin/terminal.mk-dl
/usr/share/applications/terminal.mk-dl.desktop
/usr/share/icons/hicolor/256x256/apps/terminal.mk-dl.png

%post
update-desktop-database /usr/share/applications &>/dev/null || :
gtk-update-icon-cache -f -t /usr/share/icons/hicolor &>/dev/null || :

%changelog
* Sat Jul 11 2026 terminal.mk <support@terminal.mk> - 1.0.0-1
- Initial release
