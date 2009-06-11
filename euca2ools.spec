Summary:       Elastic Utility Computing Architecture Command Line Tools
Name:          euca2ools
Version:       1.0
Release:       1
License:       MIT
Group:         Applications/System
BuildRequires: gcc, make, swig, python
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
%setup -n euca2ools

%build
cd M2Crypto-0.19.1
python setup.py build
cd ../boto-1.7a-patched
python setup.py build
cd ../euca2ools
python setup.py build

%install
cd M2Crypto-0.19.1
python setup.py install --prefix=/opt/euca2ools
cd ../boto-1.7a-patched
python setup.py install --prefix=/opt/euca2ools
cd ../euca2ools
python setup.py install --prefix=/opt/euca2ools
cd ..
mkdir /opt/euca2ools/bin
cp bin/* /opt/euca2ools/bin

%clean
rm -rf $RPM_BUILD_DIR/euca2ools
rm -rf /opt/euca2ools

%files
/opt/euca2ools

%pre

%post

%postun

%changelog
*Thu Jun 11 2009 Eucalyptus team (support@open.eucalyptus.com)
- First public release.

