Name:           terminalmk-downloader
Version:        1.1.3
Release:        1%{?dist}
Summary:        Batch downloader for terminal.mk filing attachments
License:        MIT
URL:            https://github.com/terminal-mk/downloader
BuildArch:      x86_64
Requires:       glibc

# Expects the PyInstaller onefile binary already built at
# %{_sourcedir}/terminalmk-downloader (see build_scripts/build_linux.sh).
Source0:        terminalmk-downloader

%description
Companion app for terminal.mk's CF (Corporate Filings) view. Receives a
batch handed off from the "Download All" button -- either via the
terminalmk-dl:// URL protocol or a fallback CSV -- and downloads every
attachment locally, working around browser popup/CORS limits.

%install
mkdir -p %{buildroot}/usr/bin
install -m 755 %{SOURCE0} %{buildroot}/usr/bin/terminalmk-downloader

mkdir -p %{buildroot}/usr/share/applications
cat > %{buildroot}/usr/share/applications/terminalmk-downloader.desktop <<EOF
[Desktop Entry]
Type=Application
Name=terminal.mk Downloader
Comment=Batch-downloads filing attachments handed off from terminal.mk
Exec=/usr/bin/terminalmk-downloader open %u
Terminal=false
NoDisplay=true
MimeType=x-scheme-handler/terminalmk-dl;
EOF

%files
/usr/bin/terminalmk-downloader
/usr/share/applications/terminalmk-downloader.desktop

%post
update-desktop-database /usr/share/applications &>/dev/null || :

%changelog
* Sat Jul 11 2026 terminal.mk <support@terminal.mk> - 1.1.3-1
- GUI: added drag-and-drop support for CSV files on the home screen.
- core.py: parse the compressed `dz=` terminal.mk-dl:// payload.
* Sat Jul 11 2026 terminal.mk <support@terminal.mk> - 1.0.0-1
- Initial release
