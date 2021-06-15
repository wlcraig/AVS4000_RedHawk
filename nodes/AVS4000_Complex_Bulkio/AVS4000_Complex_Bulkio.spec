# RPM package for AVS4000_Complex_Bulkio

%global _sdrroot /var/redhawk/sdr
%global _prefix %{_sdrroot}

Name: AVS4000_Complex_Bulkio
Summary: Node AVS4000_Complex_Bulkio
Version: 1.0.0
Release: 1%{?dist}
License: None
Group: REDHAWK/Nodes
Source: %{name}-%{version}.tar.gz

# Require the device manager whose SPD is referenced
Requires: DeviceManager

# Require each referenced device/service
Requires: AVS4000

BuildArch: noarch
BuildRoot: %{_tmppath}/%{name}-%{version}

%description

%prep
%setup

%install
%__rm -rf $RPM_BUILD_ROOT
%__mkdir_p "$RPM_BUILD_ROOT%{_prefix}/dev/nodes/AVS4000_Complex_Bulkio"
%__install -m 644 DeviceManager.dcd.xml $RPM_BUILD_ROOT%{_prefix}/dev/nodes/AVS4000_Complex_Bulkio/DeviceManager.dcd.xml
%__install -m 644 DeviceManager.dcd_GDiagram $RPM_BUILD_ROOT%{_prefix}/dev/nodes/AVS4000_Complex_Bulkio/DeviceManager.dcd_GDiagram
%__install -m 664 -D AVS4000_Complex_Bulkio.ini $RPM_BUILD_ROOT%{_sysconfdir}/redhawk/nodes.d/AVS4000_Complex_Bulkio.ini

%files
%defattr(-,root,redhawk)
%config(noreplace) %{_sysconfdir}/redhawk/nodes.d/AVS4000_Complex_Bulkio.ini
%defattr(-,redhawk,redhawk)
%dir %{_prefix}/dev/nodes/AVS4000_Complex_Bulkio
%{_prefix}/dev/nodes/AVS4000_Complex_Bulkio/DeviceManager.dcd.xml
%{_prefix}/dev/nodes/AVS4000_Complex_Bulkio/DeviceManager.dcd_GDiagram