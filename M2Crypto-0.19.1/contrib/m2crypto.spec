%define name    m2crypto
%define version 0.06
%define snap    snap5
%define release %{snap}.1
%define prefix  %{_prefix}

Summary:      Python crypto library
Name:         %{name}
Version:      %{version}
Release:      %{release}
Copyright:    tummy.com, ltd.
Group:        Applications/Crypto
Source:       %{name}-%{version}-%{snap}.zip
Packager:     Sean Reifschneider <jafo-rpms@tummy.com>
BuildRoot:    /var/tmp/%{name}-root
Requires:     openssl >= 0.9.6a
Patch0:       m2crypto-makefile.patch
BuildPrereq:  openssl-devel >= 0.9.6a
BuildPrereq:  swig >= 1.1p5

%description
M2Crypto makes available to the Python programmer the following:

   RSA, DH, DSA, HMACs, message digests, symmetric ciphers.
   SSL functionality to implement clients and servers.
   HTTPS extensions to Python's httplib, urllib, and the eff-bot's xmlrpclib.
   S/MIME v2.

%prep
%setup -n %{name}-%{version}-%{snap}
%patch0 -p1
%build
( cd swig; make -f Makefile.py1 )

%install
[ -n "$RPM_BUILD_ROOT" -a "$RPM_BUILD_ROOT" != / ] && rm -rf "$RPM_BUILD_ROOT"
mkdir -p "$RPM_BUILD_ROOT"/usr/lib/python1.5/site-packages
cp -a M2Crypto "$RPM_BUILD_ROOT"/usr/lib/python1.5/site-packages

%clean
[ -n "$RPM_BUILD_ROOT" -a "$RPM_BUILD_ROOT" != / ] && rm -rf "$RPM_BUILD_ROOT"

%files
%defattr(755,root,root)
%doc BUGS CHANGES INSTALL LICENCE README STORIES doc demo tests patches
/usr/lib/python1.5/site-packages
