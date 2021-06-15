# RPM package for avs4000_test_03

%global _sdrroot /var/redhawk/sdr
%global _prefix %{_sdrroot}

Name: avs4000_test_03
Summary: Waveform avs4000_test_03
Version: 1.0.3
Release: 1%{?dist}
License: None
Group: REDHAWK/Waveforms
Source: %{name}-%{version}.tar.gz

# Require the controller whose SPD is referenced
Requires: rh.ArbitraryRateResampler

# Require each referenced component
Requires: rh.TuneFilterDecimate rh.psd rh.fastfilter rh.ArbitraryRateResampler rh.AmFmPmBasebandDemod toa.DataConverter rh.sourcesocket

BuildArch: noarch
BuildRoot: %{_tmppath}/%{name}-%{version}

%description
This waveform demonstrates the AVS4000 acting as the controller of the avs400d device controller.  This means that the data is being provided to the waveform via a TCP/IP port.
  
The rh.socketSource component is used to connect and read data from the avs400d.
It is important to note that rh.sourceSocket component's properties must be updated to reflect the proper SRI for the downstream components to work properly.

Additionally the buffer sizes needed to be tweaked to support the data rate.

%prep
%setup

%install
%__rm -rf $RPM_BUILD_ROOT
%__mkdir_p "$RPM_BUILD_ROOT%{_prefix}/dom/waveforms/avs4000_test_03"
%__install -m 644 avs4000_test_03.sad.xml $RPM_BUILD_ROOT%{_prefix}/dom/waveforms/avs4000_test_03/avs4000_test_03.sad.xml
%__install -m 644 avs4000_test_03.sad_GDiagram $RPM_BUILD_ROOT%{_prefix}/dom/waveforms/avs4000_test_03/avs4000_test_03.sad_GDiagram
%__install -m 664 -D avs4000_test_03.ini $RPM_BUILD_ROOT%{_sysconfdir}/redhawk/waveforms.d/avs4000_test_03.ini

%files
%defattr(-,root,redhawk)
%config(noreplace) %{_sysconfdir}/redhawk/waveforms.d/avs4000_test_03.ini
%defattr(-,redhawk,redhawk)
%dir %{_prefix}/dom/waveforms/avs4000_test_03
%{_prefix}/dom/waveforms/avs4000_test_03/avs4000_test_03.sad.xml
%{_prefix}/dom/waveforms/avs4000_test_03/avs4000_test_03.sad_GDiagram
