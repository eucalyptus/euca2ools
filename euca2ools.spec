Summary:       Elastic Utility Computing Architecture Command Line Tools
Name:          euca2ools
Version:       1.0
Release:       1
License:       MIT
Group:         Applications/System
BuildRequires: gcc, make, swig, python-devel, python
Requires:      swig, python
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
python setup.py build
cd ../boto*
python setup.py build
cd ../euca2ools
python setup.py build

%install
cd M2Crypto-*
python setup.py install --prefix=/opt/euca2ools
cd ../boto-*
python setup.py install --prefix=/opt/euca2ools
cd ../euca2ools
python setup.py install --prefix=/opt/euca2ools
cd ..
install -g root -o root -m 755 -d /opt/euca2tools/bin
install -g root -o root -m 755 -d /opt/euca2tools/man/man1
install -g root -o root -m 755  bin/* /opt/euca2ools/bin
install -g root -o root -m 644  man/* /opt/euca2ools/man/man1

%clean
rm -rf $RPM_BUILD_DIR/euca2ools-%{version}
rm -rf /opt/euca2ools

%files
/opt/euca2ools

%changelog
*Sat Jun 27 2009 Eucalyptus Systems (support@open.eucalyptus.com)
- First public release.

