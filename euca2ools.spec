%global is_suse %(test -e /etc/SuSE-release && echo 1 || echo 0)
%global is_centos %(grep CentOS /etc/redhat-release > /dev/null && echo 1 || echo 0)
%global is_fedora %(grep Fedora /etc/redhat-release > /dev/null && echo 1 || echo 0)

%global euca_docdir    /usr/share/doc
%global euca_python    python
%global euca_where     lib/python2.6/site-packages
%global build_m2crypto 0

%ifarch x86_64
%global euca_libarch   lib64
%else
%global euca_libarch   lib
%endif

%if %is_fedora
%global build_m2crypto 0
%endif

%if %is_suse
%global euca_whereM2C  %{euca_libarch}/python2.6/site-packages
%global euca_docdir    /usr/share/doc/packages
%global build_m2crypto 1
%endif

%if %is_centos
%global euca_python    python2.5
%global euca_where     lib/python2.5/site-packages
%global euca_whereM2C  %{euca_libarch}/python2.5/site-packages
%global build_m2crypto 1
%endif

Summary:       Elastic Utility Computing Architecture Command Line Tools
Name:          euca2ools
Version:       1.3
Release:       1
License:       BSD 
Group:         Applications/System
%if %is_fedora
BuildRequires: gcc, make, swig, python-devel, python
Requires:      swig, python, m2crypto
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
Source:        http://eucalyptussoftware.com/downloads/releases/euca2ools-%{version}.tar.gz
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
%if %build_m2crypto
tar xzf deps/M2Crypto*tar.gz
%endif
tar xzf deps/boto-*tar.gz

%build
export DESTDIR=$RPM_BUILD_ROOT
%if %build_m2crypto
cd M2Crypto*
%{euca_python} setup.py build
cd ..
%endif
cd boto*
%{euca_python} setup.py build
cd ../euca2ools
%{euca_python} setup.py build
%if %is_centos
cd ..
for x in `/bin/ls bin/euca-*`; do
	sed --in-place 's:#!/usr/bin/python python:#!/usr/bin/env python2.5:' $x
done
%endif

%install
export DESTDIR=$RPM_BUILD_ROOT
%if %build_m2crypto
cd M2Crypto-*
%{euca_python} setup.py install --prefix=$DESTDIR/usr
cd ..
%endif
cd boto-*
%{euca_python} setup.py install --prefix=$DESTDIR/usr
cd ../euca2ools
%{euca_python} setup.py install --prefix=$DESTDIR/usr
cd ..
install -o root -m 755 -d $DESTDIR/usr/bin
install -o root -m 755 -d $DESTDIR/usr/man/man1
install -o root -m 755 -d $DESTDIR/%{euca_docdir}/euca2ools-%{version}
install -o root -m 755  bin/* $DESTDIR/usr/bin
install -o root -m 644  man/* $DESTDIR/usr/man/man1
install -o root -m 755  INSTALL COPYING README $DESTDIR/%{euca_docdir}/euca2ools-%{version}

%clean
[ ${RPM_BUILD_ROOT} != "/" ] && rm -rf ${RPM_BUILD_ROOT}
#export DESTDIR=$RPM_BUILD_ROOT
#rm -rf $RPM_BUILD_DIR/euca2ools-%{version}
#rm -rf $DESTDIR/%{euca_docdir}/euca2ools-%{version}
#rm -rf $DESTDIR/usr/%euca_whereM2C/M2Crypto
#rm -rf $DESTDIR/usr/%euca_whereM2C/M2Crypto*egg-info
#rm -rf $DESTDIR/usr/%euca_where/boto
#rm -rf $DESTDIR/usr/%euca_where/boto*egg-info
#rm -rf $DESTDIR/usr/%euca_where/euca2ools
#rm -rf $DESTDIR/usr/%euca_where/euca2ools*egg-info
#rm -rf $DESTDIR/usr/bin/euca-* $DESTDIR/usr/bin/s3put $DESTDIR/usr/bin/sdbadmin
#rm -rf $DESTDIR/usr/man/man1/euca-*

%files
/usr/bin/s3put
/usr/bin/sdbadmin
/usr/bin/elbadmin
/usr/bin/fetch_file
/usr/bin/launch_instance
/usr/bin/list_instances
/usr/bin/taskadmin
/usr/bin/euca-*
/usr/man/man1/euca*
%if %build_m2crypto
/usr/%euca_whereM2C/M2Crypto
/usr/%euca_whereM2C/M2Crypto*egg-info
%endif
/usr/%euca_where/boto
/usr/%euca_where/boto*egg-info
/usr/%euca_where/euca2ools
/usr/%euca_where/euca2ools*egg-info
%{euca_docdir}/euca2ools-%{version}

%changelog
* Wed Aug 18 2010 Eucalyptus Systems <support@eucalyptus.com>
- Don't build m2crypto on fedora

* Wed Mar 17 2010 Eucalyptus Systems <support@eucalyptus.com>
- Added support for fedora

* Fri Feb 12 2010 Eucalyptus Systems <support@eucalyptus.com>
- Version 1.2

* Sun Nov 1 2009 Eucalyptus Systems <support@eucalyptus.com>
- Version 1.1

* Sat Jun 27 2009 Eucalyptus Systems<(support@open.eucalyptus.com>
- First public release.

