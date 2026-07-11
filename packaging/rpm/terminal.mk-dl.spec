Name:           terminal.mk-dl
Version:        1.1.3
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
terminal.mk-dl:// URL protocol or a fallback CSV -- and downloads every
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
MimeType=x-scheme-handler/terminal.mk-dl;
EOF

%files
/usr/bin/terminal.mk-dl
/usr/share/applications/terminal.mk-dl.desktop
/usr/share/icons/hicolor/256x256/apps/terminal.mk-dl.png

%post
update-desktop-database /usr/share/applications &>/dev/null || :
gtk-update-icon-cache -f -t /usr/share/icons/hicolor &>/dev/null || :

# The .desktop file installed above only declares this app CAPABLE of
# handling x-scheme-handler/terminal.mk-dl -- it does not make it the
# DEFAULT handler, so terminal.mk-dl:// links from the browser silently
# go nowhere until something sets a default. The app can self-register
# a per-user default on first run, but %post runs as root during
# install with no real user $HOME to write to, and nothing launches the
# app to trigger that first-run registration in response to a protocol
# link it isn't registered for yet. Writing a system-wide default into
# mimeapps.list closes that gap without needing a prior launch.
SCHEME_KEY="x-scheme-handler/terminal.mk-dl"
SYSTEM_MIMEAPPS=/usr/share/applications/mimeapps.list
mkdir -p "$(dirname "$SYSTEM_MIMEAPPS")"
NEEDS_LEADING_BLANK=false
if [ -s "$SYSTEM_MIMEAPPS" ]; then
  NEEDS_LEADING_BLANK=true
fi
if [ -f "$SYSTEM_MIMEAPPS" ] && grep -q '^\[Default Applications\]' "$SYSTEM_MIMEAPPS"; then
  sed -i "\\#^${SCHEME_KEY}=#d" "$SYSTEM_MIMEAPPS"
  sed -i "/^\[Default Applications\]/a ${SCHEME_KEY}=terminal.mk-dl.desktop" "$SYSTEM_MIMEAPPS"
else
  { [ "$NEEDS_LEADING_BLANK" = true ] && echo; printf '[Default Applications]\n%s=terminal.mk-dl.desktop\n' "$SCHEME_KEY"; } >> "$SYSTEM_MIMEAPPS"
fi
command -v xdg-mime &>/dev/null && xdg-mime default terminal.mk-dl.desktop "$SCHEME_KEY" || :

%preun
if [ "$1" = "0" ]; then
  # Final removal (not just an upgrade) -- drop the default we added
  # in %post so nothing keeps pointing at an uninstalled app.
  SCHEME_KEY="x-scheme-handler/terminal.mk-dl"
  SYSTEM_MIMEAPPS=/usr/share/applications/mimeapps.list
  if [ -f "$SYSTEM_MIMEAPPS" ]; then
    sed -i "\\#^${SCHEME_KEY}=terminal.mk-dl.desktop\$#d" "$SYSTEM_MIMEAPPS" || :
  fi
fi

%changelog
* Sat Jul 11 2026 terminal.mk <support@terminal.mk> - 1.1.3-1
- GUI: added drag-and-drop support for CSV files on the home screen
  (optional tkinterdnd2 dependency; falls back to Browse/paste-link
  when it isn't installed).
- core.py: parse the compressed `dz=<base64url zlib-deflated JSON>`
  terminal.mk-dl:// payload (falls back to the older uncompressed `d=`
  param for backward compatibility).
* Sat Jul 11 2026 terminal.mk <support@terminal.mk> - 1.1.1-1
- Fixed terminal.mk-dl:// links not launching the app: %post now sets
  a system-wide default handler in mimeapps.list instead of relying on
  the app's own first-run self-registration, which never got a chance
  to run for a fresh protocol-link click.
- Added %preun cleanup of that default on removal.
* Sat Jul 11 2026 terminal.mk <support@terminal.mk> - 1.1.0-1
- Updated app icon (new gradient download glyph, matches the site's
  per-row download icon)
- Renamed the OS-level protocol scheme from terminalmk-dl to
  terminal.mk-dl (see terminalmk_downloader/protocol.py)
* Sat Jul 11 2026 terminal.mk <support@terminal.mk> - 1.0.0-1
- Initial release
