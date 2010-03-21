%global is_suse %(test -e /etc/SuSE-release && echo 1 || echo 0)
%global is_centos %(grep CentOS /etc/redhat-release > /dev/null && echo 1 || echo 0)
%global is_fedora %(grep Fedora /etc/redhat-release > /dev/null && echo 1 || echo 0)

%ifarch x86_64
%global __libarch   lib64
%else
%global __libarch   lib
%endif

%if %is_suse
%global __python    python
%global __where     lib/python2.6/site-packages
%global __whereM2C  %{__libarch}/python2.6/site-packages
%global __docdir    /usr/share/doc/packages
%endif

%if %is_centos
%global __python    python2.5
%global __where     lib/python2.5/site-packages
%global __whereM2C  %{__libarch}/python2.5/site-packages
%global __docdir    /usr/share/doc
%endif

%if %is_fedora
%global __python    python
%global __where     lib/python2.6/site-packages
%global __docdir    /usr/share/doc
%endif


Summary:       Elastic Utility Computing Architecture Command Line Tools
Name:          euca2ools
Version:       1.2
Release:       1
License:       BSD 
Group:         Applications/System
%if %is_fedora
BuildRequires: gcc, make, swig, python-devel, python, m2crypto
Requires:      swig, python
%endif
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
export DESTDIR=$RPM_BUILD_ROOT
%if %is_suse
cd M2Crypto*
%{__python} setup.py build
cd ..
%endif
%if %is_centos
cd M2Crypto*
%{__python} setup.py build
cd ..
%endif
cd boto*
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
export DESTDIR=$RPM_BUILD_ROOT
%if %is_centos
cd M2Crypto-*
%{__python} setup.py install --prefix=$DESTDIR/usr
cd ..
%endif
%if %is_suse
cd M2Crypto-*
%{__python} setup.py install --prefix=$DESTDIR/usr
cd ..
%endif
cd boto-*
%{__python} setup.py install --prefix=$DESTDIR/usr
cd ../euca2ools
%{__python} setup.py install --prefix=$DESTDIR/usr
cd ..
install -o root -m 755 -d $DESTDIR/usr/bin
install -o root -m 755 -d $DESTDIR/usr/man/man1
install -o root -m 755 -d $DESTDIR/%{__docdir}/euca2ools-%{version}
install -o root -m 755  bin/* $DESTDIR/usr/bin
install -o root -m 644  man/* $DESTDIR/usr/man/man1
install -o root -m 755  INSTALL COPYING README $DESTDIR/%{__docdir}/euca2ools-%{version}

%clean
[ ${RPM_BUILD_ROOT} != "/" ] && rm -rf ${RPM_BUILD_ROOT}
#export DESTDIR=$RPM_BUILD_ROOT
#rm -rf $RPM_BUILD_DIR/euca2ools-%{version}
#rm -rf $DESTDIR/%{__docdir}/euca2ools-%{version}
#rm -rf $DESTDIR/usr/%__whereM2C/M2Crypto
#rm -rf $DESTDIR/usr/%__whereM2C/M2Crypto*egg-info
#rm -rf $DESTDIR/usr/%__where/boto
#rm -rf $DESTDIR/usr/%__where/boto*egg-info
#rm -rf $DESTDIR/usr/%__where/euca2ools
#rm -rf $DESTDIR/usr/%__where/euca2ools*egg-info
#rm -rf $DESTDIR/usr/bin/euca-* $DESTDIR/usr/bin/s3put $DESTDIR/usr/bin/sdbadmin
#rm -rf $DESTDIR/usr/man/man1/euca-*

%files
/usr/bin/s3put
/usr/bin/sdbadmin
/usr/bin/euca-*
/usr/man/man1/euca*
%if %is_centos
/usr/%__whereM2C/M2Crypto
/usr/%__whereM2C/M2Crypto*egg-info
%endif
%if %is_suse
/usr/%__whereM2C/M2Crypto
/usr/%__whereM2C/M2Crypto*egg-info
%endif
/usr/%__where/boto
/usr/%__where/boto*egg-info
/usr/%__where/euca2ools
/usr/%__where/euca2ools*egg-info
%{__docdir}/euca2ools-%{version}

%changelog
* Wed Mar 17 2010 Eucalyptus Systems <support@eucalyptus.com>
- Added support for fedora

* Fri Feb 12 2010 Eucalyptus Systems <support@eucalyptus.com>
- Version 1.2

* Sun Nov 1 2009 Eucalyptus Systems <support@eucalyptus.com>
- Version 1.1

* Sat Jun 27 2009 Eucalyptus Systems<(support@open.eucalyptus.com>
- First public release.

