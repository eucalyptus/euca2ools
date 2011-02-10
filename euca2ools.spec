# Use Python 2.6 on el5
# Something (e.g. mock) must define el5 on that release for that check to work.
# For now we define it ourselves like this, though it means we can't build on
# RHEL 5.
%{!?el5:  %global el5  %(grep -q 'CentOS release 5' /etc/redhat-release && echo 5)}
%{!?rhel: %global rhel %(grep -q 'CentOS release 5' /etc/redhat-release && echo 5)}

%if 0%{?el5}
%global __python_ver 26
%global __python %{_bindir}/python2.6
%global __os_install_post %{?__python26_os_install_post}
%endif

%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}

Name:          euca2ools
Version:       1.3.2
Release:       0%{?dist}
Summary:       Elastic Utility Computing Architecture Command Line Tools

Group:         Applications/System
License:       BSD
URL:           http://open.eucalyptus.com
Source:        http://eucalyptussoftware.com/downloads/releases/euca2ools-%{version}.tar.gz
BuildRoot:     %(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)
BuildArch:     noarch

# %%elseif behaves like %endif followed by %if.  Avoid it to reduce confusion.

%if 0%{?el5}
BuildRequires:  python%{?__python_ver}-devel
Requires:       python%{?__python_ver}-boto >= 2.0
Requires:       python%{?__python_ver}-m2crypto >= 0.20.2
%endif
%if 0%{?rhel} > 5 || 0%{?fedora}
BuildRequires:  python-devel
Requires:       python-boto >= 2.0
Requires:       m2crypto
%endif
%if !0%{?rhel} && !0%{?fedora}
BuildRequires:  python-devel
Requires:       python-boto >= 2.0
Requires:       python-m2crypto >= 0.20.2
%endif

%description
Eucalyptus is an open source service overlay that implements elastic
computing using existing resources.  The goal of Eucalyptus is to allow
sites with existing clusters and server infrastructure to co-host elastic
computing services that are interface-compatible with Amazon's AWS (EC2,
S3, EBS).

This package contains the command line tools used to interact with
Eucalyptus.  These tools are also compatible with Amazon AWS.


%prep
%setup -q


%build
pushd %{name}
%{__python} setup.py build
popd

%if 0%{?__python_ver:1}
for file in bin/* `find %{name} -name '*.py'`; do
    sed -i '1s|^#!.*python|#!%{__python}|' $file
done
%endif


%install
rm -rf %{buildroot}
pushd %{name}
%{__python} setup.py install --prefix=%{_prefix} --skip-build --root %{buildroot}
%{__python} setup.py install -O1 --prefix=%{_prefix} --skip-build --root %{buildroot}
popd

mkdir -p %{buildroot}/%{_bindir}
mkdir -p %{buildroot}/%{_mandir}/man1
cp -p bin/* %{buildroot}/%{_bindir}
cp -p man/* %{buildroot}/%{_mandir}/man1


%clean
rm -rf %{buildroot}


%files
%defattr(-,root,root,-)
%{_bindir}/euca-*
%{_mandir}/man1/euca*
%{python_sitelib}/%{name}-*.egg-info
%{python_sitelib}/%{name}/
%doc CHANGELOG
%doc COPYING
%doc INSTALL
%doc README


%changelog
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
