# RPM package for avs4000_test_01

%global _sdrroot /var/redhawk/sdr
%global _prefix %{_sdrroot}

Name: avs4000_test_01
Summary: Waveform avs4000_test_01
Version: 1.0.3
Release: 1%{?dist}
License: None
Group: REDHAWK/Waveforms
Source: %{name}-%{version}.tar.gz

# Require the controller whose SPD is referenced
Requires: rh.TuneFilterDecimate

# Require each referenced component
Requires: rh.TuneFilterDecimate rh.psd rh.fastfilter rh.ArbitraryRateResampler rh.AmFmPmBasebandDemod toa.DataConverter

BuildArch: noarch
BuildRoot: %{_tmppath}/%{name}-%{version}

%description
This is a demonstration of the AVS4000 device connected to an AM/FM demodulator.  The AVS4000 is providing 16 I/Q complex data out of the dataShort_out port.  The default FM demodulation parameters were used.  

This waveform assumes that the AVS4000 is sending data via bukio, rather than via TCP/IP.

%prep
%setup

%install
%__rm -rf $RPM_BUILD_ROOT
%__mkdir_p "$RPM_BUILD_ROOT%{_prefix}/dom/waveforms/avs4000_test_01"
%__install -m 644 avs4000_test_01.sad.xml $RPM_BUILD_ROOT%{_prefix}/dom/waveforms/avs4000_test_01/avs4000_test_01.sad.xml
%__install -m 644 avs4000_test_01.sad_GDiagram $RPM_BUILD_ROOT%{_prefix}/dom/waveforms/avs4000_test_01/avs4000_test_01.sad_GDiagram
%__install -m 664 -D avs4000_test_01.ini $RPM_BUILD_ROOT%{_sysconfdir}/redhawk/waveforms.d/avs4000_test_01.ini

%files
%defattr(-,root,redhawk)
%config(noreplace) %{_sysconfdir}/redhawk/waveforms.d/avs4000_test_01.ini
%defattr(-,redhawk,redhawk)
%dir %{_prefix}/dom/waveforms/avs4000_test_01
%{_prefix}/dom/waveforms/avs4000_test_01/avs4000_test_01.sad.xml
%{_prefix}/dom/waveforms/avs4000_test_01/avs4000_test_01.sad_GDiagram
