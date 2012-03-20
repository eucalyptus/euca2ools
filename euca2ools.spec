# Use Python 2.6 on el5
%if 0%{?el5}
%global __python_ver 26
%global __python %{_bindir}/python2.6
%global __os_install_post %{?__python26_os_install_post}
%endif

%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}

Name:          euca2ools
Version:       2.0.1
Release:       0%{?dist}
Summary:       Elastic Utility Computing Architecture Command Line Tools

Group:         Applications/System
License:       BSD
URL:           http://open.eucalyptus.com
Source:        http://eucalyptussoftware.com/downloads/releases/euca2ools-%{version}.tar.gz
BuildRoot:     %(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)
BuildArch:     noarch

BuildRequires:  python%{?__python_ver}-devel
Requires:       python%{?__python_ver}-boto >= 2.1
Requires:       rsync
Requires:       util-linux
# %%elseif behaves like %%endif followed by %%if.  Avoid it to reduce confusion.
%if 0%{?el5}
Requires:       python%{?__python_ver}-m2crypto >= 0.20.2
%endif
%if 0%{?rhel} > 5 || 0%{?fedora}
Requires:       m2crypto
%endif
%if !0%{?rhel} && !0%{?fedora}
Requires:       python-m2crypto >= 0.20.2
%endif

Obsoletes:      euca2ools-eee < 1.3

%description
EUCALYPTUS is a service overlay that implements elastic computing
using existing resources. The goal of EUCALYPTUS is to allow sites
with existing clusters and server infrastructure to co-host an elastic
computing service that is interface-compatible with Amazon AWS.

This package contains the command line tools used to interact with
Eucalyptus.  These tools are also compatible with Amazon AWS.

%prep
%setup -q


%build
%{__python} setup.py build


%install
rm -rf %{buildroot}
%{__python} setup.py install --prefix=%{_prefix} --skip-build --root %{buildroot}
%{__python} setup.py install -O1 --prefix=%{_prefix} --skip-build --root %{buildroot}

mkdir -p %{buildroot}/%{_mandir}/man1
cp -p man/* %{buildroot}/%{_mandir}/man1


%clean
rm -rf %{buildroot}


%files
%defattr(-,root,root,-)
%{_bindir}/euare-*
%{_bindir}/euca-*
%{_bindir}/eustore-*
%{_mandir}/man1/euca*
%{_mandir}/man1/euare*
%{python_sitelib}/%{name}-*.egg-info
%{python_sitelib}/%{name}/
%doc CHANGELOG
%doc COPYING
%doc INSTALL
%doc README


%changelog
* Thu Mar 15 2012 Eucalyptus Release Engineering <support@eucalyptus.com> - 2.0.1-0.1
- Update to 2.0.1

* Tue Feb 14 2012 Eucalyptus Release Engineering <support@eucalyptus.com> - 2.0-0.2
- Fix euare-usercreate convenience options with --delegate

* Thu Feb  2 2012 Eucalyptus Release Engineering <support@eucalyptus.com> - 2.0-0.1
- Update to 2.0

* Thu Apr 21 2011 Eucalyptus Release Engineering <support@eucalyptus.com> - 1.4-0.1.alpha1
- Update to 1.4 alpha 1 (bzr rev 399)

* Thu Jan 20 2011 Eucalyptus Release Engineering <support@eucalyptus.com> - 1.3.2-0
- Update to nightly builds of 1.3.2

* Wed Aug 18 2010 Eucalyptus Systems <support@eucalyptus.com>
- Don't build m2crypto on fedora

* Wed Mar 17 2010 Eucalyptus Systems <support@eucalyptus.com>
- Added support for fedora

* Fri Feb 12 2010 Eucalyptus Systems <support@eucalyptus.com>
- Version 1.2

* Sun Nov 1 2009 Eucalyptus Systems <support@eucalyptus.com>
- Version 1.1

* Sat Jun 27 2009 Eucalyptus Systems <support@open.eucalyptus.com>
- First public release.
