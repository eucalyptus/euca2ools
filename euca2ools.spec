%define is_suse %(test -e /etc/SuSE-release && echo 1 || echo 0)
%define is_centos %(test -e /etc/redhat-release && echo 1 || echo 0)

%ifarch x86_64
%define __libarch   lib64
%else
%define __libarch   lib
%endif

%if %is_suse
%define __python    python
%define __where     %{__libarch}/python2.6/site-packages
%define __whereM2C  %{__libarch}/python2.6/site-packages
%endif

%if %is_centos
%define __python    python2.5
%define __where     lib/python2.5/site-packages
%define __whereM2C  %{__libarch}/python2.5/site-packages
%endif

Summary:       Elastic Utility Computing Architecture Command Line Tools
Name:          euca2ools
Version:       1.0
Release:       1
License:       BSD 
Group:         Applications/System
%if %is_suse
BuildRequires: gcc, make, swig, python-devel, python
Requires:      swig, python
%endif
%if %is_centos
BuildRequires: gcc, make, swig, python25-devel, python25
Requires:      swig, python25
%endif
Vendor:        Eucalyptus Systems
#Icon:          someicon.xpm
Source:        http://open.eucalyptus.com/downloads/euca2ools-%{version}.tgz
URL:           http://open.eucalyptus.com

%description
EUCALYPTUS is an open source service overlay that implements elastic
computing using existing resources. The goal of EUCALYPTUS is to allow
sites with existing clusters and server infrastructure to co-host an
elastic computing service that is interface-compatible with Amazon's EC2.

This package contains the command line tools to interact with Eucalyptus.
This tools are complatible with Amazon EC2.

%prep
%setup -n euca2ools-%{version}
tar xzf deps/M2Crypto*tar.gz
tar xzf deps/boto-*tar.gz

%build
cd M2Crypto*
%{__python} setup.py build
cd ../boto*
%{__python} setup.py build
cd ../euca2ools
%{__python} setup.py build
%if %is_centos
cd ..
for x in `/bin/ls bin/euca-*`; do
	sed --in-place 's:#!/usr/bin/env python:#!/usr/bin/env python2.5:' $x
done
%endif

%install
cd M2Crypto-*
%{__python} setup.py install --prefix=/usr
cd ../boto-*
%{__python} setup.py install --prefix=/usr
cd ../euca2ools
%{__python} setup.py install --prefix=/usr
cd ..
install -g root -o root -m 755 -d /usrbin
install -g root -o root -m 755 -d /usr/man/man1
install -g root -o root -m 755  bin/* /usr/bin
install -g root -o root -m 644  man/* /usr/man/man1

%clean
rm -rf $RPM_BUILD_DIR/euca2ools-%{version}
rm -rf /usr/%__whereM2C/M2Crypto
rm -rf /usr/%__whereM2C/M2Crypto*egg-info
rm -rf /usr/%__where/boto
rm -rf /usr/%__where/boto*egg-info
rm -rf /usr/%__where/euca2ools
rm -rf /usr/%__where/euca2ools*egg-info
rm -rf /usr/bin/euca-* /usr/local/bin/s3put /usr/local/bin/sdbadmin
rm -rf /usr/man/man1/euca-*

%files
/usr/bin/s3put
/usr/bin/sdbadmin
/usr/bin/euca-*
/usr/man/man1/euca*
/usr/%__whereM2C/M2Crypto
/usr/%__whereM2C/M2Crypto*egg-info
/usr/%__where/boto
/usr/%__where/boto*egg-info
/usr/%__where/euca2ools
/usr/%__where/euca2ools*egg-info


%changelog
*Sat Jun 27 2009 Eucalyptus Systems (support@open.eucalyptus.com)
- First public release.

