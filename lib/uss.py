DO NOT USE! Needs to be converted to a pyton module yet! 

#!/usr/bin/perl

use IO::Socket::INET;
use Socket qw(IPPROTO_TCP TCP_NODELAY);
use IO::Select;
 
use Time::HiRes qw(usleep);

use XML::Simple;
use LWP::Simple;
use JSON;

use Data::Dump qw(pp);

use POSIX qw(strftime);


my $debug = 0;

use constant { retrylimit => 10, cmdsleep=>500 }; 

use constant {
	LONG=>0, SHORT=>1, TINY=>2, VOLATILE=>3, FIX=>4,
		FLOAT=>10, STRING=>11, LISTE=>12, HASH=>13, XML=>14, DEBUG=>15,
};

my %refu_uss_kommandos={

PING => { cmd=>0, id=>0, type=>LONG, updatefreq=>VOLATILE, comment=>'USS-Ping?' },  # Firmwarepaketversion als String*23...

VERSION_1_0  => { cmd=>1, id=>0, type=>LONG, digits=>0, updatefreq=>LONG, comment=>'SR-Version' },  # 800
VERSION_1_1 => { cmd=>1, id=>1, type=>LONG, digits=>0, updatefreq=>LONG, comment=>'SR-Version'  },   # 2 
VERSION_1_2 => { cmd=>1, id=>2, type=>LONG, digits=>0, updatefreq=>LONG, comment=>'SR-Version' }, # 25
VERSION_1_3 => { cmd=>1, id=>3, type=>LONG, digits=>0, updatefreq=>LONG, comment=>'SR-Version' }, # 8
VERSION_1_4 => { cmd=>1, id=>4, type=>LONG, digits=>0, updatefreq=>LONG, comment=>'SR-Version' }, 
VERSION_1_5 => { cmd=>1, id=>5, type=>LONG, digits=>0, updatefreq=>LONG, comment=>'SR-Version' }, 

VERSION_2 => { cmd=>2, id=>0, type=>DEBUG, comment=>"Bootloader-Version",
		 paraminfo=>'<answer type="ok"><min>0</min><max>0</max><default>0</default><unit>0</unit><decimal>0</decimal><type>1030</type><arraySize>4</arraySize><flags>256</flags><check>32768</check></answer>' },

VERSION_3_0 => { cmd=>3, id=>0, type=>LONG, digits=>0, updatefreq=>LONG, comment=>'FPGA-Version', paramunit=>0, paramdecial=>0, paramtype=>1030, paramflags=>256, paramcheck=>34560 }, # 800
VERSION_3_1 => { cmd=>3, id=>1, type=>LONG, digits=>0, updatefreq=>LONG, comment=>'FPGA-Version' }, # 3 
VERSION_3_2 => { cmd=>3, id=>2, type=>LONG, digits=>0, updatefreq=>LONG, comment=>'FPGA-Version' }, # 6
VERSION_3_3 => { cmd=>3, id=>3, type=>LONG, digits=>0, updatefreq=>LONG, comment=>'FPGA-Version' }, # 4


VERSION_5_0 => { cmd=>3, id=>0, type=>LONG, digits=>0, updatefreq=>LONG, comment=>'Leistungsteil Version' }, # 800    #array14?
VERSION_5_1 => { cmd=>3, id=>1, type=>LONG, digits=>0, updatefreq=>LONG, comment=>'Leistungsteil Version' }, # 4 
VERSION_5_2 => { cmd=>3, id=>2, type=>LONG, digits=>0, updatefreq=>LONG, comment=>'Leistungsteil Version' }, # 19

#P17.0 hex-code des fehler?
#UNKNOWN_17 => { cmd=>17, id=>0, type=>DEBUG },

UNKNOWN_20 => { cmd=>20, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>1030</type><arraySize>12</arraySize><flags>38</flags><check>32775</check><name>Ger.tetyp</name></answer>' },
UNKNOWN_21 => { cmd=>21, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0</min><max>65535</max><default>0</default><unit>0</unit><decimal>0</decimal><type>1030</type><arraySize>20</arraySize><flags>37</flags><check>32775</check><name>Serialnummer des Leistungsteils</name></answer>' },
UNKNOWN_22 => { cmd=>22, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>1030</type><arraySize>8</arraySize><flags>37</flags><check>32775</check><name>Leistungselektronik-Elemente</name></answer>' },
UNKNOWN_23 => { cmd=>23, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>-3</decimal><type>34820</type><arraySize>12</arraySize><flags>35</flags><check>32775</check><name>Normierung</name></answer>' },
UNKNOWN_24 => { cmd=>24, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>-100</min><max>1000</max><default>0</default><unit>21</unit><decimal>0</decimal><type>33795</type><arraySize>10</arraySize><flags>36</flags><check>32775</check><name>UzkSchwelle</name></answer>' },



GetFirmwareVersion => 	{ special=>0x80, cmd=>0x17, id=>0x30, type=>STRING, updatefreq=>FIX, command=>'REFU.GetFirmwareVersion\n', comment=>'Firmware-Version' }, 
# \r\n"200.02.29.49"\r\n

GetFirmwareBuild => 	{ special=>0x80, cmd=>0x17, id=>0x30, type=>STRING, updatefreq=>FIX, command=>'REFU.GetFirmwareBuild\n', comment=>'Firmware-Build' }, 
# \r\n"Apr 30 2013 14:06:37"\r\n

GetCommandList => 	{ special=>0x80, cmd=>0x17, id=>0x30, type=>LISTE, updatefreq=>FIX, command=>'REFU.GetCommandList\n', comment=>'Kommando-Liste' },
# \r\n{"x","y","z"}\r\n

GetFullVersion => 	{ special=>0x80, cmd=>0x17, id=>0x30, type=>STRING, updatefreq=>FIX, command=>'REFU.GetStringParameter 0\n', comment=>'Firmwarepacketversion' },
# \r\n"RFP-802S017-29-49-S"\r\n   \r\n"RFP-802R017-29-49-S"\r\n

GetHWVersion => 	{ special=>0x80, cmd=>0x17, id=>0x30, type=>STRING, updatefreq=>FIX, command=>'REFU.GetStringParameter 20\n', comment=>'Gerätetyp' },
# \r\n"802S017"\r\n    \r\n"802R017"\r\n

GetSerialNo => 		{ special=>0x80, cmd=>0x17, id=>0x30, type=>STRING, updatefreq=>FIX, command=>'REFU.GetStringParameter 43\n', comment=>'Seriennummer des Gesamtgeräts' }, 
# \r\n"47110815"\r\n

GetStringParameter_n =>	{ special=>0x80, cmd=>0x17, id=>0x30, type=>STRING, updatefreq=>FIX, command=>'REFU.GetStringParameter %d\n', comment=>'Hole String-Parameter' }, 
GetParameter_n =>	{ special=>0x80, cmd=>0x17, id=>0x30, type=>STRING, updatefreq=>FIX, command=>'REFU.GetParameter %d\n', comment=>'Hole Parameter' }, 
GetParameter_n_m =>	{ special=>0x80, cmd=>0x17, id=>0x30, type=>STRING, updatefreq=>FIX, command=>'REFU.GetParameter %d,%d\n', comment=>'Hole Parameter mit Index' }, 
GetTime =>		{ special=>0x80, cmd=>0x17, id=>0x30, type=>STRING, updatefreq=>FIX, command=>'REFU.GetTime\n', comment=>'Hole Zeit' }, 

#"REFU.GetInitialisierungsliste",

#SetStringParameter_n =>	{ special=>0x80, cmd=>0x17, id=>0x30, type=>STRING, updatefreq=>FIX, command=>'REFU.SetStringParameter %d %s\n', comment=>'Setze String-Parameter' }, 
#SetParameter_n =>	{ special=>0x80, cmd=>0x17, id=>0x30, type=>STRING, updatefreq=>FIX, command=>'REFU.SetParameter %d,%d,%d\n', comment=>'Setze Parameter' }, 
#SetTime =>		{ special=>0x80, cmd=>0x17, id=>0x30, type=>STRING, updatefreq=>FIX, command=>'REFU.SetTime %s\n', comment=>'Setze Zeit' }, 

#"REFU.GLOBPBC_SetCountryCode",
#"REFU.SetCountryDefaultValues",

FPGA_GetVersion => 	{ special=>0x80, cmd=>0x17, id=>0x30, type=>STRING, updatefreq=>FIX, command=>'REFU.FPGA_GetVersion\n', comment=>'FPGA-Version' }, 
# \r\n"202.05.13.01"\r\n

#"REFU.FPGA_SYS_ClockInSek",

FILES_GetTextVersion =>	{ special=>0x80, cmd=>0x17, id=>0x30, type=>STRING, updatefreq=>FIX, command=>'REFU.FILES_GetTextVersion\n', comment=>'Text-Version' }, 
# \r\n"999.01.07.07"\r\n

#"REFU.FILES_GetFlash",
#"REFU.FILES_GetFlashSize",
#"REFU.FILES_GetLanguage",

#GetDisplayLanguage => 	{ special=>0x80, cmd=>0x17, id=>0x30, type=>STRING, updatefreq=>FIX, command=>'REFU.CurrentLanguage\n', comment=>'Display-Sprache' }, 
GetDisplayLanguage => 	{ special=>0x80, cmd=>0x17, id=>0x30, type=>STRING, updatefreq=>FIX, command=>'REFU.GetStringParameter 490\n', comment=>'Display-Sprache' }, 
# \r\n"de"\r\n

GetLaenderCodeListe =>	{ special=>0x80, cmd=>0x17, id=>0x30, type=>HASH, updatefreq=>FIX, command=>'REFU.GetLaendercodeListe\n', comment=>'Ländercode-Liste' }, 
# \r\n{{11,"Germany NSR",3,0}}\r\n

GetOSCI_KleinstePeriode =>{ special=>0x80, cmd=>0x17, id=>0x30, type=>STRING, updatefreq=>FIX, command=>'REFU.OSCI.KleinstePeriode \n', comment=>'OSCI-Kleinste Periode' }, 
# \r\n6.247562e-05\r\n

#"REFU.OSCI.AllocChannels",
#"REFU.OSCI.GetData",
#"REFU.OSCI.GetDataWait",
#"REFU.OSCI.InstallChannels",
#"REFU.OSCI.SetTrigger",
#"REFU.OSCI.SetZeit",
#"REFU.OSCI.Start",
#"REFU.OSCI.Status",
#"REFU.OSCI.Stop",

GetMenueTexte_n =>	{ special=>0x80, cmd=>0x17, id=>0x30, type=>HASH, updatefreq=>FIX, command=>'REFU.META_GetMenueTexte %d\n', comment=>'Menü-Texte n' }, 
# n=0 -> \r\n{{50,"Auswertung",0},{100,"Istwerte",0}}\r\n

GetStatuswortListe =>	{ special=>0x80, cmd=>0x17, id=>0x30, type=>HASH, updatefreq=>FIX, command=>'REFU.META_GetStatuswortListe\n', comment=>'StatuswortListe' }, 
GetSteuerwortListe =>	{ special=>0x80, cmd=>0x17, id=>0x30, type=>HASH, updatefreq=>FIX, command=>'REFU.META_GetSteuerwortListe\n', comment=>'SteuerwortListe' }, 


#"REFU.META_GetAuswahlMenueString",
#"REFU.META_GetBasisBild",
#"REFU.META_GetBasisBild2",
#"REFU.META_GetBfStatus",
#"REFU.META_GetMenueParListe %d",
#"REFU.META_GetMenueString",

GetMacAdress =>		{ special=>0x80, cmd=>0x17, id=>0x30, type=>STRING, updatefreq=>FIX, command=>'REFU.I2C5200_EEPROM_GetMacAddress \n', comment=>'FPGA-MAC-Adresse' }, 
# \r\n502DF4004711\r\n

# "REFU.I2C5200_EEPROM_WriteTinyString",

GetParamNummernListe =>	{ special=>0x80, cmd=>0x17, id=>0x30, type=>LISTE, updatefreq=>FIX, command=>'REFU.PARAM_GetNummernListe\n', comment=>'Parameter-Liste' }, 
# \r\n{0,1,2,3}\r\n

GetName_n =>		{ special=>0x80, cmd=>0x17, id=>0x30, type=>STRING, updatefreq=>FIX, command=>'REFU.PARAM_GetName  %d\n', comment=>'Name des Parameter n' }, 
# n=1106 -> \r\n"AC-Leistung PAC"\r\n

GetEinheitFor_n =>	{ special=>0x80, cmd=>0x17, id=>0x30, type=>STRING, updatefreq=>FIX, command=>'REFU.PARAM_GetEinheitFor %d\n', comment=>'Einheit des Parameter n' }, 
# n=1106 -> \r\n9\r\n

GetParameterInfo_n =>	{ special=>0x80, cmd=>0x17, id=>0x30, type=>XML, updatefreq=>FIX, command=>'REFU.PARAM_GetParameterInfo %d\n', comment=>'Info über Parameter n' }, 
# n=1106 -> \r\n9\r\n


#"REFU.PARAM_AutoFlushing_Disable",
#"REFU.PARAM_AutoFlushing_Enable",
#"REFU.PARAM_GetArraySizeFor %d",
#"REFU.PARAM_GetAutoFlushing",
#"REFU.PARAM_GetDatentypFor %d",
#"REFU.PARAM_GetDezimalfaktorFor %d",
#"REFU.PARAM_GetFlagsFor %d",
#"REFU.PARAM_GetFlashCounter",
#"REFU.PARAM_GetMinMaxFor %d",
#"REFU.PARAM_GetNextPNU", # 2000 -> {1193,2001}
#"REFU.PARAM_GetPasswordPNU", 2000
#"REFU.PARAM_GetRWCfor %d",
#"REFU.PARAM_GetText",
#"REFU.PARAM_KommaEinheit",
#"REFU.PARAM_Save_SR_Parameter",



GetLastErrors =>	{ special=>0x80, cmd=>0x17, id=>0x30, type=>HASH, updatefreq=>FIX, command=>'REFU.ERROR_GetLastErrors\n', comment=>'Letzte Fehler' }, 
# {{2148139274,1410424779,"Netzunterspannung LT",6,515,0,0,0,0,0,0},{2148139030,1410424778,"Unterfrequenz",6,514,0,0,0,0,0,0}}

#"REFU.ERROR_ClearErrorBuffer",
#"REFU.ERROR_GetFehlerText",
#"REFU.ERROR_GetUSSFehlertext",
#"REFU.ERROR_KillFutureTimes",


Eth_Ping =>	{ special=>0x80, cmd=>0x17, id=>0x30, type=>HASH, updatefreq=>FIX, command=>'REFU.ETH_PING %s\n', comment=>'REFU.ETH_PING IP1,I P2,IP3,IP4,Retries,Timeout' }, 

# "REFU.ETH_DNS",



#"REFU.BF_Basisbild2",
#"REFU.BF_GetBasisbildanzahl",
#"REFU.BF_GetDiagramm",
#"REFU.DATLOG_Analyse",
#"REFU.DATLOG_Format",
#"REFU.DATLOG_GetData",
#"REFU.DATLOG_KillFutureTimes",
#"REFU.DATLOG_QuickFormat",
#"REFU.DATLOG_RingLogAnalyse",
#"REFU.DATLOG_RingLog_Format",
#"REFU.DATLOG_RingLog_QuickFormat",
#"REFU.DATLOG_StopWatchdogFeed",
#"REFU.DEBUG_WS_Offline",
#"REFU.DEBUG_WS_Online",
#"REFU.EE_AC_HL_GetState",
#"REFU.EE_AC_HL_SetState",
#"REFU.EE_AC_LL_GetState",
#"REFU.EE_AC_LL_SetState",
#"REFU.EE_AC_TriggerFct",


#"REFU.STATE_TestBetriebAus",
#"REFU.STATE_TestBetriebEin",
#"REFU.Test",
#"REFU.Test_AnalogOutStart",
#"REFU.Test_AnalogOutStop",
#"REFU.Test_ANIO",
#"REFU.Test_DIGIO",
#"REFU.Test_DIGIO_GetInPort",
#"REFU.Test_DIGIO_SetCTRL",
#"REFU.Test_DIGIO_SetLedPort",
#"REFU.Test_DIGIO_SetOutPort",
#"REFU.Test_GERIO",
#"REFU.Test_GERIO_GetInPort",
#"REFU.Test_GERIO_GetInPort1",
#"REFU.Test_GERIO_GetInPort2",
#"REFU.Test_GERIO_GetInPort3",
#"REFU.Test_PWM_GERIO_OutStart",
#"REFU.Test_PWM_GERIO_OutStop",
#"REFU.Test_WS-Bus_BF_Rs485",
#"REFU.TestWSPin",
#"REFU.UPDATE_DoUpdate",
#"REFU.UPDATE_GetFirmwarepackage",
#"REFU.UPDATE_GetUpdateables",
#"REFU.UPDATE_GetUpdateProgress",
#"REFU.UPDATE_UpdateIsRunning",
#"REFU.UPDATE_USS_Masters_version"}




#"REFU.GLOBPPC_EnableDisableSelftests",
#"REFU.GLOBPPC_GetLastError",
#"REFU.GLOBPPC_GetString",
#"REFU.GLOBPPC_KillAllFutureTimes",
#"REFU.GLOBPPC_MemPoolInfo",
#"REFU.GLOBPPC_RAM_free",
#"REFU.GLOBPPC_RAM_malloc",
#"REFU.GLOBPPC_RAM_write",
#"REFU.GLOBPPC_ReadMem",
#"REFU.GLOBPPC_ReadMemoryMappedParameter",
#"REFU.GLOBPPC_Reboot",
#"REFU.GLOBPPC_Reboot_WS",
#"REFU.GLOBPPC_RebootForUpdate",
#"REFU.GLOBPPC_SetCrcCheckOnOff",
#"REFU.GLOBPPC_WriteFirmwareCrc",
#"REFU.GLOBPPC_WriteToProtectedTextArea",
#"REFU.GLOBPPC_WS_WriteFlash",
#"REFU.GLOBPPC_WSBootloaderVersion",
#"REFU.GLOBPPC_WSVersion",


#"REFU.PORTAL_CommitPortalData",
#"REFU.PORTAL_GetFlash",
#"REFU.PORTAL_GetPortalData",
#"REFU.PORTAL_PortalFalsh_KillFutureTimes",
#"REFU.PORTAL_PortalFlash_KillAllPages",
#"REFU.PORTAL_SetFlash",
#"REFU.PORTAL_Testfunktion",
#"REFU.RTS_GetLastYears",
#"REFU.RTS_KillFutureTimes",
#"REFU.SelftestStart",
#"REFU.SelftestUpdate",



UNKNOWN_26 => { cmd=>26, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>4</unit><decimal>-3</decimal><type>33795</type><arraySize>3</arraySize><flags>36</flags><check>32769</check><name>Vorladezeiten</name></answer>' },
UNKNOWN_27 => { cmd=>27, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>53</unit><decimal>-1</decimal><type>33795</type><arraySize>12</arraySize><flags>36</flags><check>32775</check><name>Innenraum Temperaturschwellen</name></answer>' },
UNKNOWN_28 => { cmd=>28, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0</min><max>16200</max><default>16000</default><unit>20</unit><decimal>0</decimal><type>1030</type><arraySize>24</arraySize><flags>38</flags><check>32769</check><name>Schalt- und Ausgangsfrequenzen</name></answer>' },
UNKNOWN_30 => { cmd=>30, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>34</unit><decimal>-1</decimal><type>1030</type><arraySize>64</arraySize><flags>38</flags><check>32775</check><name>Stromgrenzen</name></answer>' },
UNKNOWN_31 => { cmd=>31, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>1030</type><arraySize>16</arraySize><flags>38</flags><check>32769</check><name>Schaltzeiten</name></answer>' },
UNKNOWN_32 => { cmd=>32, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>34</unit><decimal>-1</decimal><type>1030</type><arraySize>1</arraySize><flags>38</flags><check>32775</check><name>Maximaler Blindstrom im FRT-Fall</name></answer>' },
UNKNOWN_33 => { cmd=>33, id=>0, type=>DEBUG, comment=>'Zulässige Einspeiseleistung',
		paraminfo=>'<answer type="ok"><min>0</min><max>65535</max><default>150</default><unit>9</unit><decimal>2</decimal><type>1030</type><arraySize>2</arraySize><flags>36</flags><check>32769</check></answer>' },
UNKNOWN_35 => { cmd=>35, id=>0, type=>DEBUG, comment=>'Produktionsdatum',
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>1030</type><arraySize>3</arraySize><flags>37</flags><check>32775</check></answer>' },
UNKNOWN_36 => { cmd=>36, id=>0, type=>DEBUG, comment=>'Offsetabgleich',
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>33795</type><arraySize>12</arraySize><flags>35</flags><check>32769</check></answer>' },
UNKNOWN_37 => { cmd=>37, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>-3</decimal><type>33795</type><arraySize>12</arraySize><flags>36</flags><check>32769</check><name>Verst.rkungsabgleich</name></answer>' },
UNKNOWN_39 => { cmd=>39, id=>0, type=>DEBUG, comment=>'Lüfter Nachlaufzeit',
		paraminfo=>'<answer type="ok"><unit>4</unit><decimal>0</decimal><type>1030</type><arraySize>1</arraySize><flags>36</flags><check>32775</check></answer>' },

NETZINDUKTIVITAET => { cmd=>40, id=>0, type=>LONG, digits=>6, scale=>1, updatefreq=>FIX, comment=>'Netzinduktivitaet', unit=>49, min=>0, max=>10000, default=>1500, flags=>38, check=>32775 },

UNKNOWN_41 => { cmd=>41, id=>0, type=>LONG, digits=>7, scale=>1, updatefreq=>FIX, comment=>'Bei Netzfrequenz wirksame Gesamtkapazit.t der Netzfilter', unit=>58, min=>0, max=>1000, default=>94, flags=>35, check=>32775 },


UNKNOWN_42 => { cmd=>42, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>-32768</min><max>32767</max><default>-1</default><unit>0</unit><decimal>0</decimal><type>33795</type><arraySize>1</arraySize><flags>37</flags><check>32775</check><name>Ausgabestand (.I)</name></answer>' },
UNKNOWN_44 => { cmd=>44, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>4</unit><decimal>-3</decimal><type>1030</type><arraySize>1</arraySize><flags>37</flags><check>32775</check><name>Selbsttest des Combiner-Relais</name></answer>' },

MAX_VOLTAGE  => { cmd=>45, id=>0, type=>FLOAT, digits=>1, scale=>10, updatefreq=>FIX, comment=>"Maximale zulässige AC Spannungen", unit=>'V' }, # id=1?

UNKNOWN_46 => { cmd=>46, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>-3</decimal><type>1030</type><arraySize>1</arraySize><flags>36</flags><check>32769</check><name>Trafo .bersetzungsfaktor</name></answer>' },
UNKNOWN_47 => { cmd=>47, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>4</unit><decimal>-3</decimal><type>2055</type><arraySize>1</arraySize><flags>32</flags><check>32768</check><name>AC-Relais-Schaltdauer</name></answer>' },
UNKNOWN_48 => { cmd=>48, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>21</unit><decimal>0</decimal><type>1030</type><arraySize>2</arraySize><flags>38</flags><check>32769</check><name>Achsen der Grenzleistungstabelle</name></answer>' },
UNKNOWN_50 => { cmd=>50, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>58</unit><decimal>-6</decimal><type>2055</type><arraySize>2</arraySize><flags>38</flags><check>32769</check><name>Zwischenkreiskapazit.t</name></answer>' },
UNKNOWN_70 => { cmd=>70, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>1030</type><arraySize>1</arraySize><flags>38</flags><check>32775</check><name>Ausblendzeit bei Hardwarest.rungen</name></answer>' },
UNKNOWN_79 => { cmd=>79, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>2055</type><arraySize>1</arraySize><flags>37</flags><check>32775</check><name>Normierungsfaktor Spannung</name></answer>' },
UNKNOWN_80 => { cmd=>80, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0</min><max>0</max><default>0</default><unit>0</unit><decimal>0</decimal><type>34820</type><arraySize>1</arraySize><flags>32</flags><check>32768</check><name>Zwischenkreisspannungsvorgabe der SR</name></answer>' },
UNKNOWN_81 => { cmd=>81, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>34820</type><arraySize>1</arraySize><flags>38</flags><check>32775</check><name>Mischvariable f.r Zwischenkreisregelung</name></answer>' },
UNKNOWN_82 => { cmd=>82, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>34820</type><arraySize>1</arraySize><flags>38</flags><check>32769</check><name>globale Aussteuergrenze f.r Stromregler</name></answer>' },
UNKNOWN_83 => { cmd=>83, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>34820</type><arraySize>1</arraySize><flags>38</flags><check>32775</check><name>Verst.rkungsfaktor d. Spannungsregler WR</name></answer>' },
UNKNOWN_84 => { cmd=>84, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0</min><max>0</max><default>0</default><unit>34</unit><decimal>0</decimal><type>34820</type><arraySize>1</arraySize><flags>32</flags><check>32768</check><name>Maximaler Sollstrom</name></answer>' },
UNKNOWN_85 => { cmd=>85, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>34820</type><arraySize>1</arraySize><flags>38</flags><check>32775</check><name>Verst.rkungsfaktor des Stromreglers</name></answer>' },
UNKNOWN_86 => { cmd=>86, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>34820</type><arraySize>1</arraySize><flags>38</flags><check>32775</check><name>Nachstellzeit des Stromreglers</name></answer>' },
UNKNOWN_87 => { cmd=>87, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0</min><max>0</max><default>0</default><unit>21</unit><decimal>-1</decimal><type>34820</type><arraySize>4</arraySize><flags>32</flags><check>32768</check><name>Zwischenkreis Eingangsspannungen</name></answer>' },
UNKNOWN_88 => { cmd=>88, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>34820</type><arraySize>1</arraySize><flags>38</flags><check>32775</check><name>Nachstellzeit des U-Reglers in int. Einh</name></answer>' },
UNKNOWN_89 => { cmd=>89, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0</min><max>0</max><default>0</default><unit>34</unit><decimal>0</decimal><type>34820</type><arraySize>2</arraySize><flags>32</flags><check>32768</check><name>Zwischenkreisstrom</name></answer>' },
UNKNOWN_90 => { cmd=>90, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0</min><max>750</max><default>0</default><unit>21</unit><decimal>0</decimal><type>34820</type><arraySize>1</arraySize><flags>35</flags><check>32775</check><name>Spannungsnormierung</name></answer>' },
UNKNOWN_91 => { cmd=>91, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0</min><max>0</max><default>0</default><unit>0</unit><decimal>0</decimal><type>34820</type><arraySize>2</arraySize><flags>32</flags><check>32768</check><name>Zwischenkreisspannung </name></answer>' },


TEMP1 => { cmd=>92, id=>0, type=>FLOAT, digits=>1, updatefreq=>SHORT, comment=>'Temperatur Kühlkörper rechts', unit=>'°C' },
TEMP2 => { cmd=>92, id=>1, type=>FLOAT, digits=>1, updatefreq=>SHORT, comment=>'Temperatur Gerät innen oben links', unit=>'°C' },
TEMP3 => { cmd=>92, id=>2, type=>FLOAT, digits=>1, updatefreq=>SHORT, comment=>'Temperatur Gerät innen unten rechts', unit=>'°C' },
TEMP4 => { cmd=>92, id=>3, type=>FLOAT, digits=>1, updatefreq=>SHORT, comment=>'Temperatur Kühlkörper links', unit=>'°C' },


UNKNOWN_93 => { cmd=>93, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>2055</type><arraySize>2</arraySize><flags>32</flags><check>32768</check><name>Fehlerstatus der WR</name></answer>' },
UNKNOWN_96 => { cmd=>96, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>2055</type><arraySize>12</arraySize><flags>38</flags><check>32775</check><name>DEBUG-Parameter des Leistungsteil</name></answer>' },
UNKNOWN_97 => { cmd=>97, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>34820</type><arraySize>7</arraySize><flags>38</flags><check>32775</check><name>WR-DebugS32</name></answer>' },
UNKNOWN_98 => { cmd=>98, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0</min><max>0</max><default>0</default><unit>1</unit><decimal>0</decimal><type>1030</type><arraySize>1</arraySize><flags>32</flags><check>32768</check><name>Fehlercode der Flashspeicherung</name></answer>' },
UNKNOWN_99 => { cmd=>99, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>2055</type><arraySize>12</arraySize><flags>38</flags><check>32775</check><name>WR Status</name></answer>' },
UNKNOWN_100 => { cmd=>100, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0</min><max>0</max><default>0</default><unit>0</unit><decimal>0</decimal><type>34820</type><arraySize>2</arraySize><flags>32</flags><check>32768</check><name>Sollspannung </name></answer>' },
UNKNOWN_101 => { cmd=>101, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0</min><max>0</max><default>0</default><unit>0</unit><decimal>0</decimal><type>34820</type><arraySize>2</arraySize><flags>32</flags><check>32768</check><name>Abweichung der Zwischenkreisspannung</name></answer>' },
UNKNOWN_102 => { cmd=>102, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0</min><max>0</max><default>0</default><unit>34</unit><decimal>0</decimal><type>34820</type><arraySize>2</arraySize><flags>32</flags><check>32768</check><name>Zwischenkreissollstrom</name></answer>' },
UNKNOWN_103 => { cmd=>103, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0</min><max>0</max><default>0</default><unit>34</unit><decimal>0</decimal><type>34820</type><arraySize>2</arraySize><flags>32</flags><check>32768</check><name>Sollstrom nach Begrenzung</name></answer>' },
UNKNOWN_104 => { cmd=>104, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0</min><max>0</max><default>0</default><unit>34</unit><decimal>0</decimal><type>34820</type><arraySize>2</arraySize><flags>32</flags><check>32768</check><name>Abweichung des Zwischenkreisstromes</name></answer>' },
UNKNOWN_105 => { cmd=>105, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0</min><max>0</max><default>0</default><unit>0</unit><decimal>0</decimal><type>34820</type><arraySize>2</arraySize><flags>32</flags><check>32768</check><name>PWM Tastgrad</name></answer>' },
UNKNOWN_106 => { cmd=>106, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0</min><max>0</max><default>0</default><unit>0</unit><decimal>0</decimal><type>34820</type><arraySize>2</arraySize><flags>32</flags><check>32768</check><name>Tasgrad nach Begrenzung</name></answer>' },
UNKNOWN_107 => { cmd=>107, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0</min><max>0</max><default>0</default><unit>0</unit><decimal>-2</decimal><type>34820</type><arraySize>2</arraySize><flags>32</flags><check>32768</check><name>Stromregler Korrekturfaktor</name></answer>' },
UNKNOWN_108 => { cmd=>108, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0</min><max>20000</max><default>0</default><unit>4</unit><decimal>-3</decimal><type>1030</type><arraySize>4</arraySize><flags>35</flags><check>32775</check><name>WR.Isolationsmessung.IsoMesszeit</name></answer>' },
UNKNOWN_109 => { cmd=>109, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>9</unit><decimal>0</decimal><type>2055</type><arraySize>66</arraySize><flags>294</flags><check>32775</check><name>Grenzleistungstabelle</name></answer>' },

UNKNOWN_110 => { cmd=>110, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0</min><max>1</max><default>0</default><unit>0</unit><decimal>0</decimal><type>1030</type><arraySize>1</arraySize><flags>35</flags><check>32775</check><name>Konfiguration Isolationsmessung</name></answer>' },

UNKNOWN_111 => { cmd=>111, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0</min><max>10000000</max><default>1100000</default><unit>51</unit><decimal>0</decimal><type>2055</type><arraySize>1</arraySize><flags>35</flags><check>32775</check><name>Isolationswiderstandsgrenze</name></answer>' },

ISOLATIONS_WIDERSTAND => { cmd=>112, id=>0, type=>DEBUG, comment=>'Gemessener Isolationswiderstand', unit=>51 },

UNKNOWN_113 => { cmd=>113, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0</min><max>2500000</max><default>643300</default><unit>51</unit><decimal>0</decimal><type>2055</type><arraySize>1</arraySize><flags>38</flags><check>32775</check><name>Eingangswiderstand der Isolationsmessung</name></answer>' },
UNKNOWN_115 => { cmd=>115, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>1030</type><arraySize>4</arraySize><flags>36</flags><check>32775</check><name>Zweigpruefung ueberspringen</name></answer>' },
UNKNOWN_116 => { cmd=>116, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>1030</type><arraySize>1</arraySize><flags>37</flags><check>32775</check><name>Isolationsmessung ueberspringen</name></answer>' },
UNKNOWN_119 => { cmd=>119, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>53</unit><decimal>-1</decimal><type>33795</type><arraySize>8</arraySize><flags>36</flags><check>32775</check><name>Temperaturgrenzen K.hler</name></answer>' },
UNKNOWN_120 => { cmd=>120, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>1030</type><arraySize>1</arraySize><flags>33</flags><check>32775</check><name>Benutzerkonfiguration des Relais K5</name></answer>' },


EINSATZLAND =>	{ cmd=>150, id=>0, type=>LONG, digits=>0, updatefreq=>LONG, comment=>'Einsatzland Ländercode' }, # 3=NSR

UNKNOWN_151 =>	{ cmd=>151, id=>0, type=>DEBUG,
			paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>2055</type><arraySize>120</arraySize><flags>37</flags><check>32775</check><name>Positivliste einstellbarer Länder</name></answer>' },

NETZSPANNUNG =>	{ cmd=>152, id=>0, type=>LONG, scale=>100*sqrt(2), digits=>2, updatefreq=>LONG, comment=>'Netzspannung Einsatzland', unit=>'V' }, 
NETZFREQUENZ =>	{ cmd=>153, id=>0, type=>LONG, scale=>100, digits=>2, updatefreq=>LONG, comment=>'Netzfrequenz Einsatzland', unit=>'s' },  


# country settings

ZUSCHALT_0 =>	{ cmd=>154, id=>0, type=>LONG, scale=>1000, digits=>3, updatefreq=>LONG, comment=>'Zuschaltzeiten', unit=>'s' },  
ZUSCHALT_1 =>	{ cmd=>154, id=>1, type=>LONG, scale=>1000, digits=>3, updatefreq=>LONG, comment=>'Zuschaltzeiten', unit=>'s' },  
ZUSCHALT_2 =>	{ cmd=>154, id=>2, type=>LONG, scale=>1000, digits=>3, updatefreq=>LONG, comment=>'Zuschaltzeiten', unit=>'s' },  
ZUSCHALT_3 =>	{ cmd=>154, id=>3, type=>LONG, scale=>1000, digits=>3, updatefreq=>LONG, comment=>'Zuschaltzeiten', unit=>'s' },  

UNKNOWN_155 => { cmd=>155, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>4</unit><decimal>-3</decimal><type>1030</type><arraySize>32</arraySize><flags>43</flags><check>32775</check><name>X-Werte der FRT-Kennlinie.</name></answer>' },
UNKNOWN_156 => { cmd=>156, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0</min><max>0</max><default>0</default><unit>21</unit><decimal>-3</decimal><type>1030</type><arraySize>32</arraySize><flags>43</flags><check>32775</check><name>Y-Werte der FRT-Kennlinie </name></answer>' },
UNKNOWN_157 => { cmd=>157, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0</min><max>100</max><default>90</default><unit>0</unit><decimal>-2</decimal><type>1030</type><arraySize>1</arraySize><flags>43</flags><check>32775</check><name>Einbruchtiefe f.r LVRT</name></answer>' },


UNKNOWN_158 => { cmd=>158, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>21</unit><decimal>-1</decimal><type>1030</type><arraySize>4</arraySize><flags>43</flags><check>32775</check><name>Umin Spannungs.berwachung.</name></answer>' },
UNKNOWN_159 => { cmd=>159, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>4</unit><decimal>-3</decimal><type>2055</type><arraySize>4</arraySize><flags>43</flags><check>32775</check><name>Tmin Spannungs.berwachung</name></answer>' },
UNKNOWN_160 => { cmd=>160, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>21</unit><decimal>-1</decimal><type>1030</type><arraySize>4</arraySize><flags>43</flags><check>32775</check><name>Umax Spannungs.berwachung</name></answer>' },
UNKNOWN_161 => { cmd=>161, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>4</unit><decimal>-3</decimal><type>2055</type><arraySize>4</arraySize><flags>43</flags><check>32775</check><name>Tmax Spannungs.berwachung</name></answer>' },
UNKNOWN_162 => { cmd=>162, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>20</unit><decimal>-2</decimal><type>1030</type><arraySize>4</arraySize><flags>43</flags><check>32775</check><name>Fmin Frequenz.berwachung</name></answer>' },
UNKNOWN_163 => { cmd=>163, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>4</unit><decimal>-3</decimal><type>2055</type><arraySize>4</arraySize><flags>43</flags><check>32775</check><name>Tmin Frequenz.berwachung</name></answer>' },
UNKNOWN_164 => { cmd=>164, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>20</unit><decimal>-2</decimal><type>1030</type><arraySize>4</arraySize><flags>43</flags><check>32775</check><name>Fmax Frequenz.berwachung</name></answer>' },
UNKNOWN_165 => { cmd=>165, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>4</unit><decimal>-3</decimal><type>2055</type><arraySize>4</arraySize><flags>43</flags><check>32775</check><name>Tmax Frequenz.berwachung</name></answer>' },
UNKNOWN_166 => { cmd=>166, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>21</unit><decimal>-1</decimal><type>1030</type><arraySize>4</arraySize><flags>43</flags><check>32775</check><name>Umin Spannungs-Mittelwert.berwachung</name></answer>' },
UNKNOWN_167 => { cmd=>167, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>4</unit><decimal>-3</decimal><type>2055</type><arraySize>4</arraySize><flags>43</flags><check>32775</check><name>Tmin Spannungs-Mittelwert.berwachung</name></answer>' },
UNKNOWN_168 => { cmd=>168, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>21</unit><decimal>-1</decimal><type>1030</type><arraySize>4</arraySize><flags>43</flags><check>32775</check><name>Umax Spannungs-Mittelwert.berwachung</name></answer>' },
UNKNOWN_169 => { cmd=>169, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>4</unit><decimal>-3</decimal><type>2055</type><arraySize>4</arraySize><flags>43</flags><check>32775</check><name>Tmax Spannungs-Mittelwert.berwachung</name></answer>' },
UNKNOWN_170 => { cmd=>170, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>21</unit><decimal>-2</decimal><type>2055</type><arraySize>4</arraySize><flags>43</flags><check>32775</check><name>Umin Aussenleiter</name></answer>' },
UNKNOWN_171 => { cmd=>171, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>4</unit><decimal>-3</decimal><type>2055</type><arraySize>4</arraySize><flags>43</flags><check>32775</check><name>TMin Aussenleiter</name></answer>' },
UNKNOWN_172 => { cmd=>172, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>21</unit><decimal>-2</decimal><type>2055</type><arraySize>4</arraySize><flags>43</flags><check>32775</check><name>UMax Aussenleiter</name></answer>' },
UNKNOWN_173 => { cmd=>173, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>4</unit><decimal>-3</decimal><type>2055</type><arraySize>4</arraySize><flags>43</flags><check>32775</check><name>TMax Aussenleiterüberwachung</name></answer>' },
UNKNOWN_174 => { cmd=>174, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>57</unit><decimal>-3</decimal><type>2055</type><arraySize>4</arraySize><flags>43</flags><check>32775</check><name>Frequenz.nderungsraten für ROCOF-Überwachung</name></answer>' },
UNKNOWN_175 => { cmd=>175, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>4</unit><decimal>-3</decimal><type>2055</type><arraySize>4</arraySize><flags>43</flags><check>32775</check><name>Beobachtungszeiten für ROCOF-Überwachung</name></answer>' },
UNKNOWN_176 => { cmd=>176, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>-3000</min><max>3000</max><default>0</default><unit>54</unit><decimal>-2</decimal><type>33795</type><arraySize>1</arraySize><flags>43</flags><check>32775</check><name>Winkeloffset Schwingkreis</name></answer>' },
UNKNOWN_177 => { cmd=>177, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>20</unit><decimal>-2</decimal><type>1030</type><arraySize>1</arraySize><flags>43</flags><check>32775</check><name>Ab dieser Frequenz wird die Wirkleistung reduziert</name></answer>' },
UNKNOWN_178 => { cmd=>178, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>20</unit><decimal>-2</decimal><type>1030</type><arraySize>2</arraySize><flags>43</flags><check>32775</check><name>Rückkehrfrequenz Leistungsreduzierung</name></answer>' },
UNKNOWN_179 => { cmd=>179, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>-2</decimal><type>1030</type><arraySize>1</arraySize><flags>43</flags><check>32775</check><name>Wirkleistungsgradient für Leistungsreduzierung</name></answer>' },
UNKNOWN_180 => { cmd=>180, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>18948</unit><decimal>-2</decimal><type>1030</type><arraySize>1</arraySize><flags>42</flags><check>32775</check><name>Umstellungszeit Landeinstellung</name></answer>' },
UNKNOWN_181 => { cmd=>181, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0</min><max>1000</max><default>0</default><unit>0</unit><decimal>-2</decimal><type>1030</type><arraySize>1</arraySize><flags>43</flags><check>32775</check><name>K-Faktor</name></answer>' },


LEISTUNGSRAMPE_ERR =>{ cmd=>182, id=>0, type=>LONG, scale=>1000, digits=>3, updatefreq=>LONG, comment=>'Leistungs-Rampenzeit nach Netzfehler', unit=>'s' }, 
LEISTUNGSRAMPE =>{ cmd=>182, id=>1, type=>LONG, scale=>1000, digits=>3, updatefreq=>LONG, comment=>'Leistungs-Rampenzeit bei Netzaufschaltung', unit=>'s' }, 

ZUSCHALT_U_L =>	{ cmd=>183, id=>0, type=>LONG, scale=>100*sqrt(2), digits=>2, updatefreq=>LONG, comment=>'Zuschaltbedingung Unterspannungsgrenze', unit=>'V' }, 
ZUSCHALT_U_H =>	{ cmd=>183, id=>1, type=>LONG, scale=>100*sqrt(2), digits=>2, updatefreq=>LONG, comment=>'Zuschaltbedingung Oberspannungsgrenze', unit=>'V' },  
ZUSCHALT_F_L =>	{ cmd=>184, id=>0, type=>LONG, scale=>100, digits=>2, updatefreq=>LONG, comment=>'Zuschaltbedingung Unterfrequenzgrenze', unit=>'Hz' }, 
ZUSCHALT_F_H =>	{ cmd=>184, id=>1, type=>LONG, scale=>100, digits=>2, updatefreq=>LONG, comment=>'Zuschaltbedingung Oberfrequenzgrenze', unit=>'Hz' },  


UNKNOWN_185 => { cmd=>185, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>-2</decimal><type>1030</type><arraySize>3</arraySize><flags>43</flags><check>32775</check><name>Wirkleistungsgradient f.r die Leistungsrampe nach Ende des frequenzabh.ngigen Leistungsderating</name></answer>' },
UNKNOWN_186 => { cmd=>186, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>4</unit><decimal>-3</decimal><type>2055</type><arraySize>1</arraySize><flags>43</flags><check>32775</check><name>Wartezeit nach Ende des frequenzabh.ngigem Leistungsderating</name></answer>' },

# end country settings

FAST_ACTIVE => { cmd=>199, id=>0, type=>DEBUG, comment=>'Schnellere Aktivierung', min=>0, max=>1, default=>0 },

UNKNOWN_200 => { cmd=>200, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>33795</type><arraySize>16</arraySize><flags>256</flags><check>34560</check><name>Analogwandler, direktes Ergebnis</name></answer>' },
UNKNOWN_201 => { cmd=>201, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0</min><max>1</max><default>0</default><unit>0</unit><decimal>0</decimal><type>517</type><arraySize>1</arraySize><flags>259</flags><check>32769</check><name>Abbruch der Initialisierung</name></answer>' },
UNKNOWN_220 => { cmd=>220, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>2055</type><arraySize>1</arraySize><flags>263</flags><check>32775</check><name>DEBUG: 256-Byte-Offset</name></answer>' },
UNKNOWN_221 => { cmd=>221, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>517</type><arraySize>65535</arraySize><flags>263</flags><check>32768</check><name>U8: Direkter Speicherzugriff</name></answer>' },
UNKNOWN_222 => { cmd=>222, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>33282</type><arraySize>65535</arraySize><flags>263</flags><check>32768</check><name>S8: Direkter Speicherzugriff</name></answer>' },
UNKNOWN_223 => { cmd=>223, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>1030</type><arraySize>65535</arraySize><flags>263</flags><check>32768</check><name>U16: Direkter Speicherzugriff</name></answer>' },
UNKNOWN_224 => { cmd=>224, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>33795</type><arraySize>65535</arraySize><flags>263</flags><check>32768</check><name>S16: Direkter Speicherzugriff</name></answer>' },
UNKNOWN_225 => { cmd=>225, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>2055</type><arraySize>65535</arraySize><flags>263</flags><check>32768</check><name>U32: Direkter Speicherzugriff</name></answer>' },
UNKNOWN_226 => { cmd=>226, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>34820</type><arraySize>65535</arraySize><flags>263</flags><check>32768</check><name>S32: Direkter Speicherzugriff</name></answer>' },
UNKNOWN_227 => { cmd=>227, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>2056</type><arraySize>65535</arraySize><flags>263</flags><check>32768</check><name>F32: Direkter Speicherzugriff</name></answer>' },
UNKNOWN_251 => { cmd=>251, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>517</type><arraySize>10</arraySize><flags>262</flags><check>34567</check><name>DEBUG Variable U8</name></answer>' },
UNKNOWN_252 => { cmd=>252, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>33282</type><arraySize>10</arraySize><flags>262</flags><check>34567</check><name>DEBUG Variable S8</name></answer>' },
UNKNOWN_253 => { cmd=>253, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>1030</type><arraySize>10</arraySize><flags>262</flags><check>34567</check><name>DEBUG Variable U16</name></answer>' },
UNKNOWN_254 => { cmd=>254, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>33795</type><arraySize>10</arraySize><flags>262</flags><check>34567</check><name>DEBUG Variable S16</name></answer>' },
UNKNOWN_255 => { cmd=>255, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>2055</type><arraySize>10</arraySize><flags>262</flags><check>34567</check><name>DEBUG Variable U32</name></answer>' },
UNKNOWN_256 => { cmd=>256, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>34820</type><arraySize>10</arraySize><flags>262</flags><check>34567</check><name>DEBUG Variable S32</name></answer>' },
UNKNOWN_257 => { cmd=>257, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>2056</type><arraySize>10</arraySize><flags>262</flags><check>34567</check><name>DEBUG-Variable F32</name></answer>' },
UNKNOWN_261 => { cmd=>261, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>517</type><arraySize>10</arraySize><flags>278</flags><check>34567</check><name>DEBUG-Variable U8 gespeichert.</name></answer>' },
UNKNOWN_262 => { cmd=>262, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>33282</type><arraySize>10</arraySize><flags>278</flags><check>34567</check><name>DEBUG-Variable S8 gespeichert.</name></answer>' },
UNKNOWN_263 => { cmd=>263, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>1030</type><arraySize>10</arraySize><flags>278</flags><check>34567</check><name>DEBUG-Variable U16 gespeichert.</name></answer>' },
UNKNOWN_264 => { cmd=>264, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>33795</type><arraySize>10</arraySize><flags>278</flags><check>34567</check><name>DEBUG-Variable S16 gespeichert.</name></answer>' },
UNKNOWN_265 => { cmd=>265, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>2055</type><arraySize>10</arraySize><flags>278</flags><check>34567</check><name>DEBUG-Variable U32 gespeichert.</name></answer>' },
UNKNOWN_266 => { cmd=>266, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>34820</type><arraySize>10</arraySize><flags>278</flags><check>34567</check><name>DEBUG-Variable S32 gespeichert.</name></answer>' },
UNKNOWN_267 => { cmd=>267, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>2056</type><arraySize>10</arraySize><flags>278</flags><check>34567</check><name>DEBUG-Variable F32 gespeichert.</name></answer>' },


UNKNOWN_300 => { cmd=>300, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0</min><max>30</max><default>5</default><unit>0</unit><decimal>-2</decimal><type>1030</type><arraySize>1</arraySize><flags>278</flags><check>32775</check><name>Beimischung der Harmonischen im FRT</name></answer>' },

LOWER_POWERREDUCTION_LIMIT => { cmd=>301, id=>0, type=>DEBUG, comment=>'Untere Grenze der Leistungsbegrenzung', min=>0, max=>100, default=>99 },

UNKNOWN_302 => { cmd=>302, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0</min><max>65535</max><default>5000</default><unit>4</unit><decimal>-3</decimal><type>1030</type><arraySize>1</arraySize><flags>17</flags><check>32775</check><name>Maximale Zeit, die der MPPT im Derating-Modus bleibt</name></answer>' },
UNKNOWN_303 => { cmd=>303, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0</min><max>1</max><default>0</default><unit>0</unit><decimal>0</decimal><type>1030</type><arraySize>1</arraySize><flags>22</flags><check>32775</check><name>Erh.hung der Scheinleistung bei cosPhi</name></answer>' },

# gridmgmt pnu

UNKNOWN_390 => { cmd=>390, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0</min><max>5000</max><default>4843</default><unit>0</unit><decimal>-4</decimal><type>1030</type><arraySize>1</arraySize><flags>17</flags><check>32775</check><name>Maximales zul.ssiges Q</name></answer>' },
UNKNOWN_391 => { cmd=>391, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0</min><max>1</max><default>0</default><unit>0</unit><decimal>0</decimal><type>1030</type><arraySize>1</arraySize><flags>17</flags><check>32775</check><name>Kennlinientyp f.r Q = f(UAC)</name></answer>' },
UNKNOWN_392 => { cmd=>392, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>21</unit><decimal>-1</decimal><type>1030</type><arraySize>4</arraySize><flags>17</flags><check>32775</check><name>Grenzpunkte f.r die Kennline Q = f(UAC)</name></answer>' },
UNKNOWN_393 => { cmd=>393, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0</min><max>100</max><default>0</default><unit>0</unit><decimal>-2</decimal><type>1030</type><arraySize>2</arraySize><flags>17</flags><check>32775</check><name>LockIn/LockOut - Schwellen f.r Q = f(UAC)</name></answer>' },
UNKNOWN_394 => { cmd=>394, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>21</unit><decimal>-1</decimal><type>1030</type><arraySize>2</arraySize><flags>17</flags><check>32775</check><name>Lock-In-Out-Schwellen f.r cosPhi = f(P)</name></answer>' },
UNKNOWN_399 => { cmd=>399, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0</min><max>180</max><default>20</default><unit>0</unit><decimal>0</decimal><type>1030</type><arraySize>11</arraySize><flags>17</flags><check>32775</check><name>.nderungsgeschwindigkeit Phasenversatz</name></answer>' },

# end gridmgmt pnu

UNKNOWN_400 => { cmd=>400, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>1030</type><arraySize>6</arraySize><flags>256</flags><check>34560</check><name>Steuer-/Statuswort</name></answer>' },
UNKNOWN_401 => { cmd=>401, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>1030</type><arraySize>6</arraySize><flags>256</flags><check>34560</check><name>Steuer-/Statuswort</name></answer>' },
UNKNOWN_402 => { cmd=>402, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>1030</type><arraySize>6</arraySize><flags>256</flags><check>34560</check><name>Steuer-/Statuswort</name></answer>' },
UNKNOWN_403 => { cmd=>403, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>1030</type><arraySize>6</arraySize><flags>256</flags><check>34560</check><name>Steuer-/Statuswort</name></answer>' },

TO_OS    => { cmd=>404, id=>2, type=>LONG, digits=>0, updatefreq=>LONG, comment=>'Verhalten Kommunikationsabbruch Bediengerät' }, # 0=ignore bei Timeout, 1=react
TO_RS485 => { cmd=>404, id=>3, type=>LONG, digits=>0, updatefreq=>LONG, comment=>'Verhalten Kommunikationsabbruch RS485' }, 
TO_USB   => { cmd=>404, id=>4, type=>LONG, digits=>0, updatefreq=>LONG, comment=>'Verhalten Kommunikationsabbruch USB' }, 
TO_ETH   => { cmd=>404, id=>5, type=>LONG, digits=>0, updatefreq=>LONG, comment=>'Verhalten Kommunikationsabbruch Ethernet' }, 


CONTROL_OS    => { cmd=>405, id=>2, type=>LONG, digits=>0, updatefreq=>LONG, comment=>'Steuerwortverhalten Bediengerät' }, # 0=ignore, 1=direct, 2=&Klemmleiste, 3=Dauer-Ein
CONTROL_RS485 => { cmd=>405, id=>3, type=>LONG, digits=>0, updatefreq=>LONG, comment=>'Steuerwortverhalten RS485' }, 
CONTROL_USB   => { cmd=>405, id=>4, type=>LONG, digits=>0, updatefreq=>LONG, comment=>'Steuerwortverhalten USB' }, 
CONTROL_ETH   => { cmd=>405, id=>5, type=>LONG, digits=>0, updatefreq=>LONG, comment=>'Steuerwortverhalten Ethernet' }, 


USS_ADDR   => { cmd=>406, id=>0, type=>LONG, digits=>0, updatefreq=>LONG, comment=>'USS-Adresse' }, # 0..31
USS_ENABLE => { cmd=>407, id=>0, type=>LONG, digits=>0, updatefreq=>LONG, comment=>'USS-Eingeschaltet', unit=>'0=aus/1=an' }, # 2=Solarlog, 3=Meteocontrol

IP_ADDR1   => { cmd=>410, id=>0, type=>LONG, digits=>0, updatefreq=>LONG, comment=>'IP-Adresse 1. Oktett' },
IP_ADDR2   => { cmd=>410, id=>1, type=>LONG, digits=>0, updatefreq=>LONG, comment=>'IP-Adresse 2. Oktett' },
IP_ADDR3   => { cmd=>410, id=>2, type=>LONG, digits=>0, updatefreq=>LONG, comment=>'IP-Adresse 3. Oktett' },
IP_ADDR4   => { cmd=>410, id=>3, type=>LONG, digits=>0, updatefreq=>LONG, comment=>'IP-Adresse 4. Oktett' },
IP_NET1    => { cmd=>411, id=>0, type=>LONG, digits=>0, updatefreq=>LONG, comment=>'Subnetzmaske 1. Oktett' },
IP_NET2    => { cmd=>411, id=>1, type=>LONG, digits=>0, updatefreq=>LONG, comment=>'Subnetzmaske 2. Oktett' },
IP_NET3    => { cmd=>411, id=>2, type=>LONG, digits=>0, updatefreq=>LONG, comment=>'Subnetzmaske 3. Oktett' },
IP_NET4    => { cmd=>411, id=>3, type=>LONG, digits=>0, updatefreq=>LONG, comment=>'Subnetzmaske 4. Oktett' },
IP_PORT    => { cmd=>412, id=>0, type=>LONG, digits=>0, updatefreq=>LONG, comment=>'Portnummer' },
IP_TIMEOUT => { cmd=>413, id=>0, type=>LONG, digits=>0, updatefreq=>LONG, comment=>'Timeout IP-Kommunikation', unit>='ms' }, 
IP_GW1     => { cmd=>414, id=>0, type=>LONG, digits=>0, updatefreq=>LONG, comment=>'IP Standard Gateway 1. Oktett' },
IP_GW2     => { cmd=>414, id=>1, type=>LONG, digits=>0, updatefreq=>LONG, comment=>'IP Standard Gateway 2. Oktett' },
IP_GW3     => { cmd=>414, id=>2, type=>LONG, digits=>0, updatefreq=>LONG, comment=>'IP Standard Gateway 3. Oktett' },
IP_GW4     => { cmd=>414, id=>3, type=>LONG, digits=>0, updatefreq=>LONG, comment=>'IP Standard Gateway 4. Oktett' },
ETH_SPEED   => { cmd=>415, id=>0, type=>LONG, digits=>0, updatefreq=>LONG, comment=>'Ethernet-Geschwindigkeit' }, # ?
IP_DNS1     => { cmd=>416, id=>0, type=>LONG, digits=>0, updatefreq=>LONG, comment=>'IP DNS-Server 1. Oktett' }, # ?
IP_DNS2     => { cmd=>416, id=>1, type=>LONG, digits=>0, updatefreq=>LONG, comment=>'IP DNS-Server 2. Oktett' },
IP_DNS3     => { cmd=>416, id=>2, type=>LONG, digits=>0, updatefreq=>LONG, comment=>'IP DNS-Server 3. Oktett' },
IP_DNS4     => { cmd=>416, id=>3, type=>LONG, digits=>0, updatefreq=>LONG, comment=>'IP DNS-Server 4. Oktett' },


UNKNOWN_420 => { cmd=>420, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>2400</min><max>115200</max><default>115200</default><unit>0</unit><decimal>0</decimal><type>2055</type><arraySize>5</arraySize><flags>273</flags><check>32775</check><name>Baudrate serielle Komm.</name></answer>' },
UNKNOWN_421 => { cmd=>421, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>1</min><max>3</max><default>2</default><unit>0</unit><decimal>0</decimal><type>517</type><arraySize>5</arraySize><flags>273</flags><check>32775</check><name>Parit.t</name></answer>' },
UNKNOWN_422 => { cmd=>422, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>1</min><max>3</max><default>1</default><unit>0</unit><decimal>0</decimal><type>517</type><arraySize>5</arraySize><flags>273</flags><check>32775</check><name>StopBits</name></answer>' },
UNKNOWN_423 => { cmd=>423, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>7</min><max>8</max><default>8</default><unit>0</unit><decimal>0</decimal><type>517</type><arraySize>5</arraySize><flags>273</flags><check>32775</check><name>Serial Bits</name></answer>' },


LOGGER_ENABLE   => { cmd=>450, id=>0, type=>LONG, digits=>0, updatefreq=>LONG, comment=>'Datenlogger', unit=>'0=aus/1=an' },
LOGGER_INTERVAL => { cmd=>451, id=>0, type=>LONG, digits=>0, updatefreq=>LONG, comment=>'Datenlogger-Intervall', unit=>'s' }, # U16 ?   30/300/600

LOGGER_PARAMETER_0  => { cmd=>452, id=>0,  type=>LONG, digits=>0, updatefreq=>LONG, comment=>'Datenlogger Parameter 0' },
LOGGER_INDEX_0      => { cmd=>453, id=>0,  type=>LONG, digits=>0, updatefreq=>LONG, comment=>'Datenlogger Index 0' },
LOGGER_PARAMETER_39 => { cmd=>452, id=>39, type=>LONG, digits=>0, updatefreq=>LONG, comment=>'Datenlogger Parameter 0' },
LOGGER_INDEX_39     => { cmd=>453, id=>39, type=>LONG, digits=>0, updatefreq=>LONG, comment=>'Datenlogger Index 0' },

UNKNOWN_454 => { cmd=>454, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0</min><max>100</max><default>0</default><unit>0</unit><decimal>0</decimal><type>517</type><arraySize>1</arraySize><flags>257</flags><check>32775</check><name>Datenlogger Zugriffsschalter</name></answer>' },

PORTAL_INTERVAL => { cmd=>470, id=>0, type=>LONG, digits=>0, updatefreq=>LONG, comment=>'Sendeintervall des Portals', unit=>'m', min=>1, max=>16000, default=>10 }, 

UNKNOWN_471 => { cmd=>471, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>517</type><arraySize>70</arraySize><flags>278</flags><check>32775</check><name>URL</name></answer>' },
UNKNOWN_472 => { cmd=>472, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0</min><max>1</max><default>0</default><unit>0</unit><decimal>0</decimal><type>517</type><arraySize>1</arraySize><flags>273</flags><check>32775</check><name>Konfigversendung</name></answer>' },
UNKNOWN_473 => { cmd=>473, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0</min><max>1</max><default>0</default><unit>0</unit><decimal>0</decimal><type>517</type><arraySize>1</arraySize><flags>17</flags><check>32775</check><name>Aktivierung des Portals</name></answer>' },
UNKNOWN_474 => { cmd=>474, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0</min><max>255</max><default>0</default><unit>0</unit><decimal>0</decimal><type>517</type><arraySize>4</arraySize><flags>22</flags><check>32775</check><name>IP-Adresse des Webportals</name></answer>' },
UNKNOWN_475 => { cmd=>475, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0</min><max>65535</max><default>0</default><unit>0</unit><decimal>0</decimal><type>1030</type><arraySize>1</arraySize><flags>22</flags><check>32775</check><name>Port des Webportals</name></answer>' },
UNKNOWN_476 => { cmd=>476, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>517</type><arraySize>1</arraySize><flags>256</flags><check>32768</check><name>Portal_State</name></answer>' },
UNKNOWN_477 => { cmd=>477, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0</min><max>1</max><default>0</default><unit>0</unit><decimal>0</decimal><type>517</type><arraySize>1</arraySize><flags>1</flags><check>32775</check><name>CommandRequestAktivierung</name></answer>' },
UNKNOWN_478 => { cmd=>478, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>1</min><max>65535</max><default>720</default><unit>17924</unit><decimal>0</decimal><type>1030</type><arraySize>1</arraySize><flags>17</flags><check>32775</check><name>Intervall des Commandrequests</name></answer>' },
UNKNOWN_479 => { cmd=>479, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>517</type><arraySize>100</arraySize><flags>278</flags><check>32775</check><name>Portal URI</name></answer>' },
UNKNOWN_490 => { cmd=>490, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0</min><max>255</max><default>0</default><unit>0</unit><decimal>0</decimal><type>1030</type><arraySize>2</arraySize><flags>17</flags><check>32775</check><name>Sprache</name></answer>' },
UNKNOWN_490 => { cmd=>490, id=>0, type=>DEBUG },

ERROR => { cmd=>500, id=>0, type=>LONG, digits=>0, updatefreq=>TINY, comment=>'Fehlercode' },
STATE => { cmd=>501, id=>0, type=>LONG, digits=>0, updatefreq=>VOLATILE, comment=>'Aktueller Betriebszustand' },

UNKNOWN_502 => { cmd=>502, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>1030</type><arraySize>1</arraySize><flags>256</flags><check>32768</check><name>Interruptrechenzeit</name></answer>' },
UNKNOWN_503 => { cmd=>503, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>53</unit><decimal>0</decimal><type>2056</type><arraySize>1</arraySize><flags>0</flags><check>32768</check><name>Temperatur Regelkarte</name></answer>' },
UNKNOWN_504 => { cmd=>504, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>517</type><arraySize>1</arraySize><flags>256</flags><check>32768</check><name>Livecontrol</name></answer>' },
UNKNOWN_505 => { cmd=>505, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>4</unit><decimal>0</decimal><type>1030</type><arraySize>1</arraySize><flags>20</flags><check>32775</check><name>Stillsetzungszeit</name></answer>' },
UNKNOWN_506 => { cmd=>506, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>9</unit><decimal>0</decimal><type>1030</type><arraySize>1</arraySize><flags>20</flags><check>32775</check><name>Leistungsgrenze</name></answer>' },
UNKNOWN_507 => { cmd=>507, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>4</unit><decimal>0</decimal><type>1030</type><arraySize>1</arraySize><flags>20</flags><check>32775</check><name>Mittelungsdauer</name></answer>' },
UNKNOWN_515 => { cmd=>515, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>1030</type><arraySize>1</arraySize><flags>19</flags><check>32775</check><name>OSCI-Aufrufintervall</name></answer>' },


UNKNOWN_600 => { cmd=>600, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>1030</type><arraySize>4</arraySize><flags>256</flags><check>34560</check><name>FPGA-Version</name></answer>' },
UNKNOWN_601 => { cmd=>601, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>2055</type><arraySize>1</arraySize><flags>256</flags><check>34560</check><name>Digitale Eing.nge der Klemmleiste</name></answer>' },
UNKNOWN_602 => { cmd=>602, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>2055</type><arraySize>1</arraySize><flags>262</flags><check>32775</check><name>Digital Ausg.nge an der Klemmleiste</name></answer>' },
UNKNOWN_801 => { cmd=>801, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>2055</type><arraySize>1</arraySize><flags>0</flags><check>34567</check><name>Bootloader-Kommunikationsparameter</name></answer>' },
UNKNOWN_802 => { cmd=>802, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>1030</type><arraySize>1</arraySize><flags>19</flags><check>32775</check><name>Bootloader-Firmware-Start</name></answer>' },
UNKNOWN_803 => { cmd=>803, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0</min><max>255</max><default>0</default><unit>0</unit><decimal>0</decimal><type>517</type><arraySize>1</arraySize><flags>22</flags><check>32775</check><name>Updatezustand</name></answer>' },
UNKNOWN_804 => { cmd=>804, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>2055</type><arraySize>4</arraySize><flags>275</flags><check>32775</check><name>Update CRC Check</name></answer>' },
UNKNOWN_810 => { cmd=>810, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>2056</type><arraySize>65535</arraySize><flags>256</flags><check>32768</check><name>Bitte ignorieren!</name></answer>' },


UNKNOWN_1000 => { cmd=>1000, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>2055</type><arraySize>4</arraySize><flags>36</flags><check>32775</check><name>Aufzeichnungskanal 1</name></answer>' },
UNKNOWN_1001 => { cmd=>1001, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>2055</type><arraySize>4</arraySize><flags>36</flags><check>32775</check><name>Aufzeichnungskanal 2</name></answer>' },
UNKNOWN_1002 => { cmd=>1002, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>2055</type><arraySize>4</arraySize><flags>36</flags><check>32775</check><name>Aufzeichnungskanal 3</name></answer>' },
UNKNOWN_1003 => { cmd=>1003, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>2055</type><arraySize>4</arraySize><flags>36</flags><check>32775</check><name>Aufzeichnungskanal 4</name></answer>' },
UNKNOWN_1004 => { cmd=>1004, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>2055</type><arraySize>4</arraySize><flags>36</flags><check>32775</check><name>Triggerkanal</name></answer>' },
UNKNOWN_1005 => { cmd=>1005, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>1030</type><arraySize>1</arraySize><flags>36</flags><check>32775</check><name>Abtastperiode</name></answer>' },
UNKNOWN_1006 => { cmd=>1006, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>34820</type><arraySize>1</arraySize><flags>36</flags><check>32775</check><name>Triggerschwelle</name></answer>' },
UNKNOWN_1007 => { cmd=>1007, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0</min><max>511</max><default>0</default><unit>0</unit><decimal>0</decimal><type>1030</type><arraySize>1</arraySize><flags>36</flags><check>32775</check><name>Trigger-Delay</name></answer>' },
UNKNOWN_1008 => { cmd=>1008, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>1030</type><arraySize>1</arraySize><flags>36</flags><check>32775</check><name>Triggerbedingung</name></answer>' },
UNKNOWN_1009 => { cmd=>1009, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0</min><max>0</max><default>0</default><unit>0</unit><decimal>0</decimal><type>2055</type><arraySize>512</arraySize><flags>32</flags><check>32768</check><name>Datenkanal 1 und 2</name></answer>' },
UNKNOWN_1010 => { cmd=>1010, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0</min><max>0</max><default>0</default><unit>0</unit><decimal>0</decimal><type>2055</type><arraySize>512</arraySize><flags>32</flags><check>32768</check><name>Datenkanal 3 und 4</name></answer>' },
UNKNOWN_1021 => { cmd=>1021, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>-50</min><max>50</max><default>10</default><unit>0</unit><decimal>0</decimal><type>33795</type><arraySize>11</arraySize><flags>276</flags><check>32775</check><name>Blindstromkompensation wenn induktiv</name></answer>' },
UNKNOWN_1022 => { cmd=>1022, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>-50</min><max>50</max><default>10</default><unit>0</unit><decimal>0</decimal><type>33795</type><arraySize>11</arraySize><flags>276</flags><check>32775</check><name>Blindstrom kompensation f.r kapazitiv</name></answer>' },



#ENS_START  => { cmd=>900, id=>0, type=>LONG, digits=>0, updatefreq=>LONG, comment=>'Start ENS-Test',  unit=>'0=aus/1=an' },
#ENS_STATUS => { cmd=>901, id=>0, type=>LONG, digits=>0, updatefreq=>TINY, comment=>'Zustand ENS-Test' },
#ENS_FREQ   => { cmd=>902, id=>0, type=>FLOAT, digits=>2, updatefreq=>TINY, comment=>'Verlauf Simulierte Frequenz', unit=>'Hz' },
#ENS_FREQL  => { cmd=>903, id=>0, type=>FLOAT, digits=>2, updatefreq=>LONG, comment=>'Frequenzwert Abschaltung unteren Grenze', unit=>'Hz' },
#ENS_FREQH  => { cmd=>903, id=>1, type=>FLOAT, digits=>2, updatefreq=>LONG, comment=>'Frequenzwert Abschaltung obere Grenze', unit=>'Hz' },
#ENS_U      => { cmd=>904, id=>0, type=>FLOAT, digits=>2, updatefreq=>TINY, comment=>'Verlauf Simulierte Spannung', unit=>'V' },
#ENS_UL     => { cmd=>905, id=>0, type=>FLOAT, digits=>2, updatefreq=>LONG, comment=>'Spannungswert Abschaltung unteren Grenze', unit=>'V' },
#ENS_UH     => { cmd=>905, id=>1, type=>FLOAT, digits=>2, updatefreq=>LONG, comment=>'Spannungswert Abschaltung obere Grenze', unit=>'V' },
#ENS_FREQ_D => { cmd=>908, id=>0, type=>FLOAT, digits=>2, updatefreq=>TINY, comment=>'Frequenzrampe', unit=>'mHz/s' },
#ENS_U_D    => { cmd=>909, id=>0, type=>FLOAT, digits=>2, updatefreq=>TINY, comment=>'Spannungsrampe', unit=>'mV/s' },
#ENS_T_FL   => { cmd=>910, id=>0, type=>FLOAT, digits=>2, updatefreq=>TINY, comment=>'Messzeit bis Frequenzuntergrenze erreicht', unit=>'s' }, # s?
#ENS_T_FH   => { cmd=>910, id=>1, type=>FLOAT, digits=>2, updatefreq=>TINY, comment=>'Messzeit bis Frequenzobergrenze erreicht', unit=>'s' },
#ENS_T_UL   => { cmd=>910, id=>2, type=>FLOAT, digits=>2, updatefreq=>TINY, comment=>'Messzeit bis Spannungsuntergrenze erreicht', unit=>'s' },
#ENS_T_UH   => { cmd=>910, id=>3, type=>FLOAT, digits=>2, updatefreq=>TINY, comment=>'Messzeit bis Spannungsobergrenze erreicht', unit=>'s' },


UNKNOWN_1101 => { cmd=>1101, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><unit>21</unit><decimal>0</decimal><type>1030</type><arraySize>7</arraySize><flags>275</flags><check>32769</check><name>Schwellwerte f.r Betriebszust.nde</name></answer>' },

U_ZW      => { cmd=>1100, id=>0, type=>FLOAT, digits=>2, updatefreq=>TINY, comment=>'Istwerte der Zwischenkreisspannung',  unit=>'V' }, #array 4?
UAC_L1    => { cmd=>1102, id=>0, type=>FLOAT, digits=>0, updatefreq=>TINY, comment=>'Netzspannung UAC L1',  unit=>'V' },
UAC_L2    => { cmd=>1102, id=>1, type=>FLOAT, digits=>0, updatefreq=>TINY, comment=>'Netzspannung UAC L2',  unit=>'V' },
UAC_L3    => { cmd=>1102, id=>2, type=>FLOAT, digits=>0, updatefreq=>TINY, comment=>'Netzspannung UAC L3',  unit=>'V' },
IAC_L1    => { cmd=>1103, id=>0, type=>FLOAT, digits=>0, updatefreq=>TINY, comment=>'Istwert des Netzstroms IAC L1',  unit=>'A' },
IAC_L2    => { cmd=>1103, id=>1, type=>FLOAT, digits=>0, updatefreq=>TINY, comment=>'Istwert des Netzstroms IAC L2',  unit=>'A' },
IAC_L3    => { cmd=>1103, id=>2, type=>FLOAT, digits=>0, updatefreq=>TINY, comment=>'Istwert des Netzstroms IAC L3',  unit=>'A' },
UDC       => { cmd=>1104, id=>0, type=>FLOAT, digits=>2, updatefreq=>TINY, comment=>'DC Spannung',  unit=>'V' },
IDC       => { cmd=>1105, id=>0, type=>FLOAT, digits=>2, updatefreq=>TINY, comment=>'DC Stromstärke',  unit=>'A' },
PAC       => { cmd=>1106, id=>0, type=>FLOAT, digits=>0, updatefreq=>TINY, comment=>'AC-Leistung PAC',  unit=>'W' },
PDC       => { cmd=>1107, id=>0, type=>FLOAT, digits=>0, updatefreq=>TINY, comment=>'DC Leistung',  unit=>'W' },

UNKNOWN_1108 => { cmd=>1108, id=>0, type=>DEBUG, comment=>'Fehlerstrom lt. AFI-Baugruppe',
		paraminfo=>'<answer type="ok"><min>0.000000</min><max>0.000000</max><default>0.000000</default><unit>34</unit><decimal>0</decimal><type>2056</type><arraySize>1</arraySize><flags>256</flags><check>32768</check></answer>' },
UNKNOWN_1109 => { cmd=>1109, id=>0, type=>DEBUG, comment=>'Aussenleiter Netzspannung',
		paraminfo=>'<answer type="ok"><min>0.000000</min><max>0.000000</max><default>0.000000</default><unit>21</unit><decimal>0</decimal><type>2056</type><arraySize>1</arraySize><flags>257</flags><check>32768</check></answer>' },

UNKNOWN_1110 => { cmd=>1110, id=>0, type=>DEBUG, comment=>'Die Begrenzungen des Leistungssollwertes',
		paraminfo=>'<answer type="ok"><min>0.000000</min><max>0.000000</max><default>0.000000</default><unit>9</unit><decimal>0</decimal><type>2056</type><arraySize>7</arraySize><flags>256</flags><check>32768</check></answer>' },
UNKNOWN_1111 => { cmd=>1111, id=>0, type=>DEBUG, comment=>'',
		paraminfo=>'<answer type="ok"><min>0</min><max>0</max><default>0</default><unit>9</unit><decimal>0</decimal><type>2055</type><arraySize>3</arraySize><flags>256</flags><check>32768</check><name>Leistungsbegrenzung durch die Betriebsart</name></answer>' },

PHASE_L1  => { cmd=>1120, id=>0, type=>FLOAT, digits=>2, updatefreq=>TINY, comment=>'Phasenwinkel L1',  unit=>'°' },
PHASE_L2  => { cmd=>1120, id=>1, type=>FLOAT, digits=>2, updatefreq=>TINY, comment=>'Phasenwinkel L2',  unit=>'°' },
PHASE_L3  => { cmd=>1120, id=>2, type=>FLOAT, digits=>2, updatefreq=>TINY, comment=>'Phasenwinkel L3',  unit=>'°' },
UAC_L1    => { cmd=>1121, id=>0, type=>FLOAT, digits=>2, updatefreq=>TINY, comment=>'AC Spannung Peak L1',  unit=>'V' }, # *sqrt(2)/2
UAC_L2    => { cmd=>1121, id=>1, type=>FLOAT, digits=>2, updatefreq=>TINY, comment=>'AC Spannung Peak L2',  unit=>'V' },
UAC_L3    => { cmd=>1121, id=>2, type=>FLOAT, digits=>2, updatefreq=>TINY, comment=>'AC Spannung Peak L3',  unit=>'V' },
FREQ_L1   => { cmd=>1122, id=>0, type=>FLOAT, digits=>2, updatefreq=>TINY, comment=>'Frequenz L1',  unit=>'Hz' },
FREQ_L2   => { cmd=>1122, id=>1, type=>FLOAT, digits=>2, updatefreq=>TINY, comment=>'Frequenz L2',  unit=>'Hz' },
FREQ_L3   => { cmd=>1122, id=>2, type=>FLOAT, digits=>2, updatefreq=>TINY, comment=>'Frequenz L3',  unit=>'Hz' },

UAC_1     => { cmd=>1123, id=>0, type=>FLOAT, digits=>2, updatefreq=>TINY, comment=>'AC Effektivspannung Mittelwert',  unit=>'V' },
IAC_1     => { cmd=>1124, id=>0, type=>FLOAT, digits=>2, updatefreq=>TINY, comment=>'AC Stromstärke Summe L1+L2+L3',  unit=>'A' },


UNKNOWN_1129 => { cmd=>1129, id=>0, type=>DEBUG, comment=>'Maximaler DC-Symmetriestrom',
		paraminfo=>'<answer type="ok"><unit>34</unit><decimal>-3</decimal><type>1030</type><arraySize>2</arraySize><flags>278</flags><check>32775</check></answer>' },
UNKNOWN_1130 => { cmd=>1130, id=>0, type=>DEBUG, comment=>'Proportionalfaktor für Stromregler',
		paraminfo=>'<answer type="ok"><min>0</min><max>5000</max><default>500</default><unit>0</unit><decimal>-3</decimal><type>1030</type><arraySize>2</arraySize><flags>276</flags><check>32775</check></answer>' },
UNKNOWN_1132 => { cmd=>1132, id=>0, type=>DEBUG, comment=>'Proportionalfaktor f.r Symmetrierregler',
		paraminfo=>'<answer type="ok"><min>0</min><max>1000</max><default>90</default><unit>0</unit><decimal>-2</decimal><type>1030</type><arraySize>2</arraySize><flags>276</flags><check>32775</check></answer>' },
UNKNOWN_1133 => { cmd=>1133, id=>0, type=>DEBUG, comment=>'Integralfaktor Bypass-Regler Symmetrier.',
		paraminfo=>'<answer type="ok"><min>0</min><max>1000</max><default>20</default><unit>0</unit><decimal>-6</decimal><type>1030</type><arraySize>1</arraySize><flags>276</flags><check>32775</check></answer>' },
UNKNOWN_1134 => { cmd=>1134, id=>0, type=>DEBUG, comment=>'P-Anteil des DC-Reglers für MPP-Tracker',
		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>1030</type><arraySize>1</arraySize><flags>22</flags><check>32775</check></answer>' },
UNKNOWN_1135 => { cmd=>1135, id=>0, type=>DEBUG, comment=>'Nachstellzeit DC-Regler für MPP-Tracker',
		paraminfo=>'<answer type="ok"><min>0</min><max>65535</max><default>0</default><unit>4</unit><decimal>-3</decimal><type>1030</type><arraySize>1</arraySize><flags>22</flags><check>32775</check></answer>' },
UNKNOWN_1136 => { cmd=>1136, id=>0, type=>DEBUG, comment=>'Max_dP_dt',
		paraminfo=>'<answer type="ok"><min>0</min><max>60000</max><default>30</default><unit>20</unit><decimal>-2</decimal><type>1030</type><arraySize>2</arraySize><flags>278</flags><check>32775</check></answer>' },
UNKNOWN_1137 => { cmd=>1137, id=>0, type=>DEBUG, comment=>'HSS-Strom-abhangige Leistungsreduzierung',
		paraminfo=>'<answer type="ok"><min>0</min><max>1000</max><default>16</default><unit>20</unit><decimal>-2</decimal><type>1030</type><arraySize>2</arraySize><flags>278</flags><check>32775</check></answer>' },
UNKNOWN_1138 => { cmd=>1138, id=>0, type=>DEBUG, comment=>'HSS-Auslastungsgrenze Leistungsreduktion',
		paraminfo=>'<answer type="ok"><min>0</min><max>1200</max><default>1007</default><unit>0</unit><decimal>-3</decimal><type>1030</type><arraySize>1</arraySize><flags>278</flags><check>32775</check></answer>' },
UNKNOWN_1139 => { cmd=>1139, id=>0, type=>DEBUG, comment=>'Sollwertvorgabe des Hochsetzstellers',
		paraminfo=>'<answer type="ok"><min>10</min><max>105</max><default>65</default><unit>21</unit><decimal>0</decimal><type>1030</type><arraySize>1</arraySize><flags>278</flags><check>32775</check></answer>' },



IAC_M     => { cmd=>1140, id=>0, type=>FLOAT, digits=>2, updatefreq=>TINY, comment=>'AC Stromstärke Phase Mittelwert *3', _unit=>'A',
		paraminfo=>'<answer type="ok"><min>0</min><max>1000</max><default>0</default><unit>0</unit><decimal>-3</decimal><type>34820</type><arraySize>4</arraySize><flags>275</flags><check>32775</check><name>.berblender f.r dU/dt-Vorsteuerung</name></answer>' },

IAC_L1    => { cmd=>1141, id=>0, type=>FLOAT, digits=>2, updatefreq=>TINY, comment=>'AC Stromstärke L1', unit=>'A' },
IAC_L2    => { cmd=>1141, id=>1, type=>FLOAT, digits=>2, updatefreq=>TINY, comment=>'AC Stromstärke L2', unit=>'A' },
IAC_L3    => { cmd=>1141, id=>2, type=>FLOAT, digits=>2, updatefreq=>TINY, comment=>'AC Stromstärke L3', unit=>'A' },

UNKNOWN_1142 => { cmd=>1142, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0.000000</min><max>0.000000</max><default>0.000000</default><unit>9</unit><decimal>0</decimal><type>2056</type><arraySize>2</arraySize><flags>256</flags><check>32768</check><name>Gesamtleistung</name></answer>' },
UNKNOWN_1143 => { cmd=>1143, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0.000000</min><max>0.000000</max><default>0.000000</default><unit>34</unit><decimal>0</decimal><type>2056</type><arraySize>1</arraySize><flags>256</flags><check>32768</check><name>Symmetrieregler-Ausgabe</name></answer>' },
UNKNOWN_1144 => { cmd=>1144, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0</min><max>65535</max><default>6000</default><unit>9</unit><decimal>0</decimal><type>1030</type><arraySize>1</arraySize><flags>276</flags><check>32775</check><name>dP_dt_Fensterradius</name></answer>' },
UNKNOWN_1145 => { cmd=>1145, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0</min><max>100</max><default>10</default><unit>0</unit><decimal>-3</decimal><type>1030</type><arraySize>1</arraySize><flags>22</flags><check>32775</check><name>Minimal-Modulationsgrad</name></answer>' },
UNKNOWN_1146 => { cmd=>1146, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0</min><max>1000</max><default>0</default><unit>21</unit><decimal>0</decimal><type>1030</type><arraySize>2</arraySize><flags>20</flags><check>32775</check><name>Grenzsspannung Hochsetztstellerregler</name></answer>' },
UNKNOWN_1147 => { cmd=>1147, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0</min><max>0</max><default>0</default><unit>21</unit><decimal>0</decimal><type>2055</type><arraySize>1</arraySize><flags>260</flags><check>32768</check><name>Sollwert UzkHigh</name></answer>' },


COS_PHI_IST => { cmd=>1149, id=>0, type=>FLOAT, digits=>2, updatefreq=>VOLATILE, comment=>'Winkelversatz Ist' },

E_TAG    => { cmd=>1150, id=>0, type=>FLOAT, digits=>1, updatefreq=>SHORT, comment=>'Tagesertrag',   unit=>'kWh' },
E_GESTERN=> { cmd=>1150, id=>1, type=>FLOAT, digits=>1, updatefreq=>SHORT, comment=>'Tagesertrag gestern',   unit=>'kWh' }, # ?

E_OPHOURS => { cmd=>1152, id=>0, type=>FLOAT, digits=>0, updatefreq=>LONG,  comment=>'Betriebsstunden',  unit=>'h' },

E_MONAT  => { cmd=>1153, id=>0, type=>FLOAT, digits=>1, updatefreq=>LONG,  comment=>'Monatsertrag',  unit=>'kWh' },
E_JAHR   => { cmd=>1154, id=>0, type=>FLOAT, digits=>1, updatefreq=>LONG,  comment=>'Jahressertrag', unit=>'kWh' },
E_GESAMT => { cmd=>1151, id=>0, type=>FLOAT, digits=>1, updatefreq=>LONG,  comment=>'Gesamtertrag',  unit=>'kWh' },

E_NORM   => { cmd=>1155, id=>0, type=>FLOAT, digits=>2, updatefreq=>LONG,  comment=>'Normierung Ertrag/Nennleistung Generator', unit=>'kWp' }, # für 1150..1154

E_TAG_DC  => { cmd=>1156, id=>0, type=>FLOAT, digits=>1, updatefreq=>SHORT, comment=>'Tagessonnenenergie',  unit=>'kWh' },

# grid mgmt pnu
UNKNOWN_1158 => { cmd=>1158, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>-500</min><max>500</max><default>0</default><unit>0</unit><decimal>-1</decimal><type>34820</type><arraySize>1</arraySize><flags>273</flags><check>32775</check><name>Gespeicherte Q Vorgabe</name></answer>' },


UNKNOWN_1159 => { cmd=>1159, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>-500</min><max>500</max><default>0</default><unit>0</unit><decimal>-1</decimal><type>34820</type><arraySize>1</arraySize><flags>256</flags><check>32775</check><name>Q Vorgabe</name></answer>' },
UNKNOWN_1160 => { cmd=>1160, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>-5000</min><max>5000</max><default>0</default><unit>0</unit><decimal>0</decimal><type>33795</type><arraySize>35</arraySize><flags>278</flags><check>34567</check><name>cosphi Kompensationstabelle</name></answer>' },

PAC_SOLL => { cmd=>1161, id=>0, type=>LONG, digits=>1, updatefreq=>VOLATILE, comment=>'Leistungssollwert', unit=>'W' },

PAC_LIMIT => { cmd=>1162, id=>0, type=>LONG, digits=>0, updatefreq=>VOLATILE,  comment=>'Leistungsbegrenzung PMU', unit=>'0.1%' }, # 0..1000 für 0..100% (min 5%)

PAC_CLIENT => { cmd=>1163, id=>0, type=>LONG, digits=>0, updatefreq=>VOLATILE, comment=>'Leistungsbegrenzung Kunde', unit=>'%' },


# grid mgmt pnu

UNKNOWN_1164 => { cmd=>1164, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0</min><max>10</max><default>0</default><unit>0</unit><decimal>0</decimal><type>517</type><arraySize>1</arraySize><flags>273</flags><check>32775</check><name>Auswahlmen. Winkelversatz</name></answer>' },

UNKNOWN_1165 => { cmd=>1165, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>-3000</min><max>3000</max><default>0</default><unit>54</unit><decimal>-2</decimal><type>33795</type><arraySize>1</arraySize><flags>273</flags><check>32775</check><name>Anlagespez. Offset Phasenverschiebung</name></answer>' },

#COS_PHI_FIX  => { cmd=>1166, id=>0,  type=>LONG, digits=>0, updatefreq=>LONG,  comment=>'Fixer cos phi als Winkel', unit=>'°'  }, 
#COS_PHI_VAR  => { cmd=>1167, id=>0,  type=>LONG, digits=>0, updatefreq=>LONG,  comment=>'Winkelversatz variabel über PMU' }, 
#COS_PHI_P    => { cmd=>1168, id=>0,  type=>LONG, digits=>0, updatefreq=>LONG,  comment=>'Winkelversatz über P-Kennlinie' }, 
#COS_PHI_P_1  => { cmd=>1168, id=>1,  type=>LONG, digits=>0, updatefreq=>LONG,  comment=>'Winkelversatz über P-Kennlinie', unit=>'°' }, 
#COS_PHI_P_10 => { cmd=>1168, id=>10, type=>LONG, digits=>0, updatefreq=>LONG,  comment=>'Winkelversatz über P-Kennlinie', unit=>'°' }, 
#COS_PHI_U    => { cmd=>1169, id=>0,  type=>LONG, digits=>0, updatefreq=>LONG,  comment=>'Winkelversatz über U-Kennlinie' }, 
#COS_PHI_U_1  => { cmd=>1169, id=>1,  type=>LONG, digits=>0, updatefreq=>LONG,  comment=>'Winkelversatz über U-Kennlinie', unit=>'°' }, 
#COS_PHI_U_10 => { cmd=>1169, id=>10, type=>LONG, digits=>0, updatefreq=>LONG,  comment=>'Winkelversatz über U-Kennlinie', unit=>'°' }, 

# end grid mgmt

UNKNOWN_1170 => { cmd=>1170, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0</min><max>20</max><default>1</default><unit>0</unit><decimal>0</decimal><type>517</type><arraySize>5</arraySize><flags>276</flags><check>32775</check><name>MPPT Einstellungen</name></answer>' },
UNKNOWN_1171 => { cmd=>1171, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0</min><max>2549</max><default>0</default><unit>20</unit><decimal>0</decimal><type>1030</type><arraySize>4</arraySize><flags>277</flags><check>32775</check><name>Grenzfrequenzen</name></answer>' },
UNKNOWN_1172 => { cmd=>1172, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0</min><max>16000</max><default>1000</default><unit>21</unit><decimal>-3</decimal><type>1030</type><arraySize>4</arraySize><flags>278</flags><check>32775</check><name>Inkremente</name></answer>' },
UNKNOWN_1173 => { cmd=>1173, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0</min><max>15000</max><default>100</default><unit>0</unit><decimal>0</decimal><type>1030</type><arraySize>2</arraySize><flags>278</flags><check>32775</check><name>Vorsteuerung MPPT</name></answer>' },
UNKNOWN_1174 => { cmd=>1174, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0</min><max>10000</max><default>1500</default><unit>0</unit><decimal>0</decimal><type>1030</type><arraySize>2</arraySize><flags>278</flags><check>32775</check><name>Schwellen</name></answer>' },
UNKNOWN_1175 => { cmd=>1175, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>200</min><max>1500</max><default>500</default><unit>21</unit><decimal>0</decimal><type>1030</type><arraySize>2</arraySize><flags>278</flags><check>32775</check><name>MPP Spannungsbereich</name></answer>' },
UNKNOWN_1177 => { cmd=>1177, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>200</min><max>1250</max><default>850</default><unit>21</unit><decimal>0</decimal><type>1030</type><arraySize>1</arraySize><flags>278</flags><check>32775</check><name>Spg. Startwert</name></answer>' },
UNKNOWN_1178 => { cmd=>1178, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0</min><max>850</max><default>200</default><unit>21</unit><decimal>0</decimal><type>1030</type><arraySize>1</arraySize><flags>278</flags><check>32775</check><name>Spg. Endwert</name></answer>' },
UNKNOWN_1179 => { cmd=>1179, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>200</min><max>850</max><default>660</default><unit>21</unit><decimal>0</decimal><type>1030</type><arraySize>1</arraySize><flags>276</flags><check>32775</check><name>Sollwert bei man. DC-Spannungsvorgabe</name></answer>' },
UNKNOWN_1180 => { cmd=>1180, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>10</min><max>200</max><default>86</default><unit>0</unit><decimal>-1</decimal><type>1030</type><arraySize>1</arraySize><flags>19</flags><check>32775</check><name>Minimale Leistung f.r Volllastbetrieb</name></answer>' },
UNKNOWN_1181 => { cmd=>1181, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0</min><max>1000</max><default>8</default><unit>0</unit><decimal>0</decimal><type>1030</type><arraySize>1</arraySize><flags>22</flags><check>32775</check><name>Maximale Asymmetrie f.r Phasenaktivierung</name></answer>' },
UNKNOWN_1182 => { cmd=>1182, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>-1.000000</min><max>20.000000</max><default>0.000000</default><unit>0</unit><decimal>0</decimal><type>2056</type><arraySize>6</arraySize><flags>262</flags><check>32768</check><name>Allg. Tracker-.berwachungen</name></answer>' },
UNKNOWN_1183 => { cmd=>1183, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0.000000</min><max>0.000000</max><default>0.000000</default><unit>21</unit><decimal>0</decimal><type>2056</type><arraySize>8</arraySize><flags>262</flags><check>32768</check><name>Spg. .berwachung Tracker</name></answer>' },
UNKNOWN_1184 => { cmd=>1184, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0.000000</min><max>0.000000</max><default>0.000000</default><unit>34</unit><decimal>0</decimal><type>2056</type><arraySize>5</arraySize><flags>262</flags><check>32768</check><name>Strom .berwachungen Tracker</name></answer>' },
UNKNOWN_1185 => { cmd=>1185, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0.000000</min><max>0.000000</max><default>0.000000</default><unit>9</unit><decimal>0</decimal><type>2056</type><arraySize>10</arraySize><flags>262</flags><check>32768</check><name>Leistungs .berwachung</name></answer>' },
UNKNOWN_1186 => { cmd=>1186, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>4</min><max>500</max><default>6</default><unit>0</unit><decimal>0</decimal><type>1030</type><arraySize>2</arraySize><flags>278</flags><check>32775</check><name>MPPT Frequenzen</name></answer>' },
UNKNOWN_1187 => { cmd=>1187, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0</min><max>10000</max><default>20</default><unit>9</unit><decimal>0</decimal><type>1030</type><arraySize>1</arraySize><flags>278</flags><check>32775</check><name>MPPT Grenzen</name></answer>' },
UNKNOWN_1188 => { cmd=>1188, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0</min><max>10000</max><default>600</default><unit>4</unit><decimal>0</decimal><type>1030</type><arraySize>1</arraySize><flags>278</flags><check>32775</check><name>Mittelungszeit f.r die Leistungsasymmetrie</name></answer>' },
UNKNOWN_1189 => { cmd=>1189, id=>0, type=>DEBUG, 
		paraminfo=>'<answer type="ok"><min>0</min><max>100</max><default>0</default><unit>0</unit><decimal>0</decimal><type>1030</type><arraySize>1</arraySize><flags>278</flags><check>32775</check><name>Erlaubte Leistungsasymmetrie</name></answer>' },


SENSOR1_CONF_0 => 	{ cmd=>1190, id=>0, type=>FLOAT, digits=>3, updatefreq=>FIX, comment=>'Sensor 1 Offset', unit=>'mV' }, # 0 
SENSOR1_CONF_1 => 	{ cmd=>1190, id=>1, type=>FLOAT, digits=>3, updatefreq=>FIX, comment=>'Sensor 1 Normierung Zähler', unit=>'W/m²' }, # 130
SENSOR1_CONF_2 => 	{ cmd=>1190, id=>2, type=>FLOAT, digits=>3, updatefreq=>FIX, comment=>'Sensor 1 Normierung Nenner', unit=>'mV' }, # 1

SENSOR1  => 		{ cmd=>1191, id=>0, type=>FLOAT, digits=>1, updatefreq=>SHORT, comment=>'Einstrahlung', unit=>'W/m²' }, # 0-10V => 0-1300 W/m²

SENSOR2_CONF_0 => 	{ cmd=>1192, id=>0, type=>FLOAT, digits=>3, updatefreq=>FIX, comment=>'Sensor 2 Offset', unit=>'mV' }, # -2,268
SENSOR2_CONF_1 => 	{ cmd=>1192, id=>1, type=>FLOAT, digits=>3, updatefreq=>FIX, comment=>'Sensor 2 Normierung Zähler', unit=>'°C' }, # 1
SENSOR2_CONF_2 => 	{ cmd=>1192, id=>2, type=>FLOAT, digits=>3, updatefreq=>FIX, comment=>'Sensor 2 Normierung Nenner', unit=>'mV' }, # 87

SENSOR2 => 		{ cmd=>1193, id=>0, type=>FLOAT, digits=>1, updatefreq=>SHORT, comment=>'Modul-Temperatur',  unit=>'°C' }, #  0-10V => -26,1°C – 90°C

PASSWORD => 		{ cmd=>2000, id=>0, type=>LONG, digits=>0, updatefreq=>LONG,  comment=>'Passwortebene' }, 
PASSWORD_TO => 		{ cmd=>2001, id=>0, type=>LONG, digits=>0, updatefreq=>LONG,  comment=>'Passwortgültigkeitsdauer', unit=>'s', min=>10, max=>60000, default=>3600 },

};


#my %ENSteststatus={
#0 => 'Initialisierung / Startbereit', 1..3 'Frequenztest zur unteren Frequenzgrenze', 4..6 'Frequenztest zur oberen Frequenzgrenze',
#7..9 'Spannungstest zur unteren Spannungsgrenze', 10..12 'Spannungstest zur oberen Spannungsgrenze', 13 => 'ENS-Test beendet' };


# Antwort von: REFU.META_GetSteuerwortListe  (Bits?)
my $SteuerwortListe={
	0 => 'Ein',
	1 => 'nAus1',
	2 => 'nAus2',
	3 => 'Betrieb An',
	4 => '-',
	5 => '-',
	6 => '-',
	7 => 'Störung quittieren',
	8 => 'K5',
	9 => 'K1',
	10 => 'K3',
	11 => 'EN_WR',
	12 => '-',
	13 => '-',
	14 => '-',
	15 => '-'
};


# Antwort von: REFU.META_GetStatuswortListe	(Bits?)
my $StatuswortListe={
	0 => 'Einschaltbereit',
	1 => 'Betriebsbereit',
	2 => 'Betrieb',
	3 => 'Störung',
	4 => 'Aktivierung',
	5 => 'Erdschluss',
	6 => 'Einschaltsperre',
	7 => 'Achtung',
	8 => 'Kurzausfall',
	9 => 'Parametrierung über REMOTE',
	10 => '-',
	11 => 'ZwPr',
	12 => 'Symmetrierung',
	13 => 'Isolationsprüfung',
	14 => 'Service',
	15 => 'Befehl über serielle Schnittstelle',
};



sub make_hashliste($$)
{
	my %hash;
	my $keycol=$_[1];
	foreach ( @{ @_[0] } ) { $hash{ $_->[$keycol] } = $_; }
	return \%hash;
}

sub make_hashscalar($)
{
	my %hash;
	foreach ( @{ @_[0] } ) { $hash{ $_->[0] } = $_->[1]; } 
	return \%hash;
}

sub parserefuanswer_hash0($)
{
	my $answerstring=$_[0];
	$answerstring =~ s#\"#\'#go;
	$answerstring =~ s#\s*\{(\d+)\s*\,(.*?)}\s*(,|\n)#\1 => \[ \2 \],#go;
	return eval $answerstring;
}


sub parserefuanswer_liste($)
{
	my $answerstring=$_[0];
	$answerstring =~ s#\"#\'#go;
	$answerstring =~ s#\{#\[#go;
	$answerstring =~ s#\}#\]#go;
	return eval $answerstring;
}


# Antwort von: REFU.GetLaendercodeListe
my $LaendercodeListe = make_hashliste( parserefuanswer_liste('
{{0,"Austria",23,0},{1,"Australia",4,0},{2,"Belgium",5,0},{3,"Bosnia",53,0},{4,"Bulgaria",20,0},{5,"China",7,0},{6,"Croatia",51,0},{7,"Cyprus",33,0},
{8,"Czech Republic",6,0},{9,"Denmark",43,0},{10,"Estonia",44,0},{11,"France",10,0},{12,"French Islands 50Hz",39,0},{13,"French Islands 60Hz",40,0},
{14,"Germany ENS",1,0},{15,"Germany MSR",2,0},{16,"Germany NSR",3,0},
{17,"Greece Continent",11,0},{18,"Greek Islands",12,0},{19,"Hungary",31,0},{20,"India",34,0},{21,"Israel",13,0},{22,"Italy DK5940",14,0},
{23,"Italy CEI 021",47,0},{24,"Italy CEI 021 Isla.",48,0},{25,"Latvia",45,0},{26,"Lithuania",46,0},{27,"Luxembourg",21,0},{28,"Malaysia IQCC",62,0},
{29,"Malaysia TNB",63,0},{30,"Morocco",55,0},{31,"Netherlands",22,0},{32,"Philippines",42,0},{33,"Poland",54,0},{34,"Portugal",17,0},{35,"Romania",24,0},
{36,"Saudi Arabia",35,0},{37,"Serbia",52,0},{38,"Singapore G59/2",60,0},{39,"Singapore G83/2",61,0},{40,"Slovakia",25,0},{41,"Slovenia",18,0},
{42,"South Africa",57,0},{43,"South Korea",16,0},{44,"Spain RD1663",8,0},{45,"Spain RD1699",56,0},{46,"Spain RD661",9,0},{47,"Sweden",27,0},
{48,"Switzerland",28,0},{49,"Taiwan",36,0},{50,"Thailand MEA",37,0},{51,"Thailand PEA",38,0},{52,"Tunisia",30,0},{53,"Turkey",29,0},{54,"United Kingdom",32,0},,,,,}
'), 2);




use constant {
	PWD_ANY => 0, # 0x0 0
	PWD_USER => 72555, # 0x11b6b 1

  # other passwords stripped...
  #INSTALLER #SERVICEPARTNER #SERVICE #PRODUCTION #DEVELOPMENT #PWD_DEVELOPMENT_OLD #DEBUG #COUNTRYCODE #LIMIT #INIT #PWD_SPCOUNTRYCODE #PWD_SPCOUNTRYCODE2 #PWD_SPCOUNTRYCODE3 #PWD_SPCOUNTRYSETTINGS #PWD_SPCOUNTRYSETTINGS2 #PWD_SPCOUNTRYSETTINGS3

	PWD_INIT => 0, # 0x0 15 ???????
};


my %USSerrorcodes = (
	-1=>"unbekannter Fehler.",
	0=>"Unzulässige PNU",
	1=>"PNU nicht änderbar",
	2=>"ausserhalb Min/Max",
	3=>"falscher Index",
	4=>"Kein Arrayparameter",
	5=>"falscher Datentyp",
	6=>"kein Setzen erlaubt",
	7=>"Text nicht änderbar",
	11=>"Keine Bedienhoheit",
	12=>"Passwort falsch; PNU kann nicht beschrieben werden. Falsche Passwortebene.",
);


sub getChecksum($)
{
	my $result=0;
	foreach (@{$_[0]}) { $result ^= $_; }
	return $result & 0xff;
}


sub createMessage($$$$$)
{
	my ($ak, $id, $index, $longValue, $rtpbytes)=@_;

	$longValue=0 unless $longValue;

	my $ussadr = 0;

	# AK
	# 0x00 				kein auftrag
	# 0x10 				PWE anforderung 16/32 bit
	# 0x20 				PWE schreiben 16 bit (wort 4)
	# 0x30 				PWE schreiben 32 bit (wort 3 und 4)
	# 0x60 fetch   0x0110xxxx  	pwe anfordern array 2
	# 0x70 update  0x0111xxxx   	pwe schreiben array 2 16bit
	# 0x80 update  			pwe schreiben array 2 32 bit
	# 0x90 request array length?	anzahl elemente des array

	my $isbroadcast = 0x20 * 0;
	my $ismirror    = 0x40 * 0;
	my $isspecial   = 0x80 * 0;

	$isspecial = 0x80 if defined($rtpbytes);

	my @bytes=(

		0x02, # Start Of Text (STX)
		0x00, # Platzhalter für Telegramlänge (LGE)
		$ussadr & 0x1f | $isbroadcast | $ismirror | $isspecial , # Adresse ADR

		# Begin Nutzdaten

		# PKE
		$ak | ($id & 0xFF00) / 0x100,		# PKE H
		$id & 0x00FF,				# PKE L
	);

	if(defined $rtpbytes) {
	
	push @bytes, unpack "C*", $rtpbytes;

	} else {

	# USS Type 2 4/6 Worte
	push @bytes,
		(	
		
		# IND
		($index & 0xFF00) / 0x100,		# IND H	
		$index & 0x00FF,			# IND L
	
		# PKW
		($longValue / 0x1000000) & 0xFF, 
		($longValue / 0x10000) & 0xFF, 
		($longValue / 0x100) & 0xFF, 
		($longValue ) & 0xFF, 
		
		# PZD
		0x00, 0x00,
		0x00, 0x00,
		0x00, 0x00,
		0x00, 0x00,
		0x00, 0x00,
		0x00, 0x00,

		# Ende Nutzdaten
	);

	}

	$bytes[1] = $#bytes +1-1 ; # Telegramlänge (ohne STX und LGE) 

	push @bytes, getChecksum(\@bytes); # Checksumme (BCC)

	if($debug) {
	print "Request (".(1+$#bytes)."): ";
	printf "%2.2x ", $_ for @bytes;
	print "\n";
	}

	return \@bytes;
}




sub net_send($$)
{
	my $socket=$_[0];
	my $req=pack('C*', @{ $_[1] });

	# two characters delay
	usleep(1000* cmdsleep ); # 500ms

	my $size = $socket->send( $req );
	printf STDERR "sent data %d of length %d\n", $size, length($req) if($debug);
}


sub net_receive($)
{
	my $select = $_[0];
	my $returnbuf;
	
	for my $sock ($select->can_read(20)){
		my $buf;
		
 		$sock->recv($buf, 256); my $len=length($buf);
# 		my $len=$sock->read($buf, 256);
		print STDERR "received data of length $len\n" if($debug);
		$returnbuf.=$buf;
	}
	return $returnbuf;
}



sub parseMessage($$)
{
	my @response=unpack 'C*', $_[0];
	my $sentrequest=$_[1];

	if($debug) {
	print "Reponse (".(1+$#response)."): ";
	printf "%2.2x ", $_ for @response;
	print "\n";
	}

	return 1 if ((1+$#response)==0); # empty

	my $crcfield = pop @response;
	my $crccalc = getChecksum( \@response );

	if($crcfield != $crccalc)
	{
		print STDERR "Error: BCC/CRC wrong\n";
		return 1; # DATAERR
	}

	my $isbroadcast = ($response[2] & 0x20);
	my $ismirror = ($response[2] & 0x40);
	my $isspecial = ($response[2] & 0x80);

	if($debug) {
#	print "CRC: $crcfield $crccalc\n";
#	print "STX: ".$response[0]."\n";
#	print "LGE: ".$response[1]."\n";
	print "ADR: ".($response[2] & 0x1f)."\n";

	print "ADR: Broadcast\n" if ($isbroadcast);
	print "ADR: Mirror\n" if ($ismirror);
	print "ADR: Special\n" if ($isspecial);
	}

	my $typ = $response[3]; # special type
	my $ak = $response[3] & 0xF0; # Auftrags/Antwortkennung

	printf "AK: %x\n", $ak if($debug);

	my $id = ($response[3] & 0x07) * 0x100 + $response[4]; # PNU
	my $flags = $response[4]; # RTP flags/counter
	my $index = $response[5] * 0x100 + $response[6]; 
	my $value = $response[7] * 0x1000000 + $response[8] * 0x10000 + $response[9] * 0x100 + $response[10];   # pkw

	my $sentak  = $sentrequest->[3] & 0xf0;
	my $sentspecial = $sentrequest->[2] & 0x80;
	my $sentcounter = $sentrequest->[4] & 0xf;
	my $sentid = (($sentrequest->[3]) & 0x7) * 0x100 + $sentrequest->[4];
	my $sentidx = $sentrequest->[5] * 0x100 + $sentrequest->[6];


	# 0x10 wort übertragen
	# 0x20 doppelwort übertragen


	if($ak == 0x00)  # dummy/ping 
	{
		printf "dummy/ping id $id index $index pwe $value\n" if($debug);

		if($sentak!=$ak or $sentid!=$id or $sentidx!=$index) {
			print STDERR "Error: was old result...\n" if ($debug);
			return 1; #DATAERR
		}
		return 0; # OK
	}


	if($ak == 0x70)  # auftrag nicht ausführbar mit fehlernummer
	{
		printf STDERR "Error: Auftrag nicht ausführbar für id $id index $index errorcode $value, %s\n", ( $USSerrorcodes{$value}||$USSerrorcodes{-1} );

		return 3; # ERR
	}

	if($ak == 0x80)  # keine PKW Bedienhoheit
	{
		printf STDERR "Error: Keine Bedienhoheit für id $id index $index \n";

		return 3; # ERR
	}


	if($ak == 0x50 or $ak == 0x40)  # 0101xxxx pwe uebertragen array doppelwort  (40=wort)
	{

		if($sentid!=$id or $sentidx!=$index) {
			print STDERR "Error: was old result...\n" if ($debug);
			return 1; # DATAERR
		}

		my $floatvalue = unpack "f", pack "C4", $response[10], $response[9], $response[8], $response[7]; # endianess ....

		$status = $response[11] * 0x100 + $response[12];
		$fehler = $response[13] * 0x100 + $response[14];
		$acleistung = $response[15] * 0x100 + $response[16];
		$uac = $response[17] * 0x100 + $response[18];
		$spannungdc = $response[19] * 0x100 + $response[20];
		$ptoday = $response[21] * 0x100 + $response[22];

		printf "id $id index $index longvalue $value float=%.7f    status $status fehler $fehler pac $acleistung uac10 $uac udc $spannungdc ptoday $ptoday \n", $floatvalue;

		return 0; # OK
	}

	# RTP response
	if ( $isspecial && $typ==0x17 )
	{
		my $counter=$flags & 0xf;

		if($counter != $sentcounter) {
			print STDERR "RTP reponse, counter mismatch\n" if ($debug);
			return 1; # DATAERR
		} else {

			my $firstflag=$flags & 0x10;
			my $lastflag=$flags & 0x20;
			my $moreflag=$flags & 0x40;

			my $rtpresponse = '';
			$rtpresponse = pack "C*", @response[5..$#response] if ($#response>4);

			printf "RTP response: first %x last %x more %x counter $counter data __%s__\n", $firstflag, $lastflag, $moreflag, $rtpresponse if($debug);

			return [ $flags, $rtpresponse ];

		}
	}

	print "ERROR, unknown response\n";

	return 2; # UNKNOWN (yet) unknown answer
}


sub ping($$)
{
        my ($socket, $select)=@_;

	my $msg= createMessage(0x0, 0 ,0, undef, undef);
	my $recbuf;
	my $pingcnt=0;
	do {
		net_send($socket, $msg);
		$recbuf = net_receive($select); 
		$pingcnt++;
	}
	while (parseMessage($recbuf, $msg) > 0 and $pingcnt<retrylimit);

	return ($pingcnt>=retrylimit);
}




sub requestUSS($$$$)
{
        my ($socket, $select, $id, $index)=@_;

	print "USS Request: id $id index $index\n"; 
		
	my $msg= createMessage(0x60, $id, $index, 0, undef);
	my $recbuf;
	my $reqcnt=0;
	do {
		net_send($socket, $msg);
		$recbuf = net_receive($select); 
		$reqcnt++;
	}
	while (parseMessage($recbuf, $msg) > 0 and $reqcnt<retrylimit);

	print STDERR "Error: max request num\n" if ($reqcnt>=retrylimit);

	return ($reqcnt>=retrylimit);

}


sub updateUSS($$$$$)
{
        my ($socket, $select, $id, $index, $value)=@_;

	print "USS Update: id $id index $index value $value\n"; 
		
	my $msg= createMessage( 0x80, $id, $index, $value, undef);
	my $recbuf;
	my $reqcnt=0;
	my $ret;
	do {
		net_send($socket, $msg);
		$recbuf = net_receive($select); 
		$reqcnt++;

		$ret=parseMessage($recbuf, $msg); 
	}
	while ( ($ret==1) and $reqcnt<retrylimit);

	print STDERR "Error: failed\n" if ($ret!=0);
	print STDERR "Error: max request num\n" if ($reqcnt>=retrylimit);

	return ($reqcnt>=retrylimit);

}




# RTP via USS transport
sub sendRTP($$$)
{
        my ($socket, $select, $rtpcommand)=@_;

	my $ak=0x17;
	my $id=0x0;

	$rtpcommand.="\n" if(substr($rtpcommand,-1,1) ne "\n");

	print "RTP request: $rtpcommand"; 
		
        my $rtpcmds = int(length($rtpcommand)/244) + ((length($rtpcommand)%244)>0?1:0);
        my $letzterunde = ($rtpcmds==1);
        my $runde=0;

	my $answer;

        while($runde<$rtpcmds) {
                my $cmdoffset=$runde*244;
                my $cmdlength=($runde<$rtpcmds-1)?244:length($rtpcommand)-$cmdoffset;

                my $cmdtosend=substr($rtpcommand, $cmdoffset, $cmdlength);

                my $id = $runde % 16;
                $id|=0x10          if ($runde==0); # first
                $id|=0x20          if ($runde==$rtpcmds-1); # last
                $letzterunde=true     if ($runde==$rtpcmds-1);

		my $rtpmsg= createMessage($ak, $id, undef, undef, $cmdtosend);

		my $sendcnt=0;
		my $parseret;
		do {

			net_send($socket, $rtpmsg); 
			my $rtprecbuf = net_receive($select); 

			$parseret = parseMessage($rtprecbuf, $rtpmsg);

			if( ref($parseret) ne 'ARRAY' ) {
				print STDERR "Error while sending RTP, retrying\n";
			}

			$sendcnt++;
		} while( (ref($parseret) ne 'ARRAY') and ($sendcnt<retrylimit) );

		if( ($parseret->[0] & 0x70) == 0x0) { # weder first, last noch more
			print STDERR "Error in response RTP\n";
		}

		my $rtpresponse=$parseret->[1];

		if (($parseret->[0] & 0x10) == 0x10) # first
		{
			$answer=$rtpresponse;
		} else {
			$answer.=$rtpresponse;
		}

		$letzterunde=0 if (($parseret->[0] & 0x20) == 0x20); # fuer die naechste schleife ist das die letzte runde

		$runde++;
        }

	my $respcnt=1;
	while($letzterunde and ($respcnt<500))  # $letzterunde hier invertiert
	{
                my $id = $runde % 16;
                $id|=0x40; # more

		my $rtpmsg= createMessage($ak, $id, undef, undef, '');
		net_send($socket, $rtpmsg); 
		my $rtprecbuf = net_receive($select); 
		my $parseret = parseMessage($rtprecbuf, $rtpmsg);

		if( ref($parseret) ne 'ARRAY') {
			print STDERR "Error while sending RTP\n";
			$letzterunde=0;
		}

		#if( ($parseret->[0] & 0x70) == 0x0) { # weder first, last noch more
		#	print STDERR "Error in response RTP\n";
		#	$letzterunde=0;
		#}

		my $rtpresponse=$parseret->[1];

		if (($parseret->[0] & 0x10) == 0x10) # first
		{
			$answer=$rtpresponse;
		} else {
			$answer.=$rtpresponse;
		}

		$letzterunde=0 if (($parseret->[0] & 0x20) == 0x20);

		$runde++;
		$respcnt++;
	}

	# trim
	$answer =~ s/^( |\n|\r)+//go;
	$answer =~ s/( |\n|\r)+$//go;


	printf "RTP answer: $answer\n"; # %x , $answer;
	
	return $answer;
}


STDOUT->autoflush(1);
STDERR->autoflush(1);


# auto-flush on socket
$| = 1;

my $socket = new IO::Socket::INET (

	#    PeerHost => '172.23.84.35',  # WR3 Kokisch
    #PeerHost => '172.23.16.191',  # WR3 Kokisch via relay

	#PeerHost => '172.23.77.33',  # nm16
	#PeerHost => '172.23.77.41',  # lg9

	#PeerHost => '172.23.74.33',  # lx16 zschettgau
	#PeerHost => '172.23.74.34',
	#PeerHost => '172.23.74.35',
	#PeerHost => '172.23.74.36',
	
	#PeerHost => '172.23.85.33',
	#PeerHost => '172.23.85.34',
	#PeerHost => '172.23.85.41',

	#PeerHost => '172.23.70.52',  # sas14w 7018
	#PeerHost => '172.23.70.36',  # sas8w 3340

	# PeerHost => '172.23.66.33',  # wörbzig 1
	
	#PeerHost => '172.23.90.34',  # bs1 13

	#PeerHost => '172.23.88.33',  # ploetzkau 1
	#PeerHost => '172.23.88.34',  # ploetzkau 2

    #PeerHost => '192.168.10.92', # ersatz von refu
    #PeerHost => '172.23.80.92', # Refu dirk
    #PeerHost => '172.23.80.93', # PVM dirk
    #PeerHost => '172.23.83.33',
    #PeerHost => '172.23.74.36', # WR lx16 MSR (2) statt 3
    #PeerHost => '172.23.74.33', # WR lx16 Austria (23)
	
	#PeerHost => '172.23.94.33', # Refu Keller AF30

	#PeerHost => '192.168.130.20', # default ip new
	#PeerHost => '192.168.0.123',  # default ip old

#	PeerHost => '172.23.91.33', # refu neu willerstedt
	#PeerHost => '172.23.91.34', # refu neu willerstedt
	PeerHost => '172.23.91.35', # refu neu willerstedt

	#PeerHost => '172.23.101.33', # großmühlingen
#	PeerHost => '172.23.101.34', # großmühlingen

	#PeerHost => '172.23.102.33', # Drosa
	#PeerHost => '172.23.102.34', # Drosa

#	PeerHost => '172.23.64.33', # Crüchern


	
    PeerPort => '21062',
    Proto => 'tcp',
#	Blocking => 1,
);
die "cannot connect $!\n" unless $socket;
print "Connected to the inverter.\n";

#my $select = IO::Select->new();
#$select->add($socket);

my $select = new IO::Select($socket);


$socket->setsockopt(IPPROTO_TCP, TCP_NODELAY, 1); 
$socket->blocking(0);
$socket->autoflush(1);



ping($socket,$select);

=begin comment

sendRTP($socket,$select, "REFU.GetParameter 150\n");
#sendRTP($socket,$select, "REFU.PORTAL_Testfunktion\n");
#sendRTP($socket,$select, "REFU.GetLaendercodeListe\n");

requestUSS($socket,$select, 150,0 );
requestUSS($socket,$select, 180,0 );
requestUSS($socket,$select, 1152,0 );

requestUSS($socket,$select, 40,0 );


requestUSS($socket,$select, 1,0 );
requestUSS($socket,$select, 1,1 );
requestUSS($socket,$select, 1,2 );
requestUSS($socket,$select, 1,3 );
requestUSS($socket,$select, 1,4 );
requestUSS($socket,$select, 1,5 );

requestUSS($socket,$select, 2,0 );

requestUSS($socket,$select, 3,0 );
requestUSS($socket,$select, 3,1 );
requestUSS($socket,$select, 3,2 );
requestUSS($socket,$select, 3,3 );

requestUSS($socket,$select, 5,0 );
requestUSS($socket,$select, 5,1 );
requestUSS($socket,$select, 5,2 );

=cut



#RTP request: REFU.GetStringParameter 20
#RTP answer: ""
#RTP request: REFU.GetStringParameter 43
#RTP answer: ""


sendRTP($socket,$select, "REFU.GetStringParameter 20\n");  # device type



sendRTP($socket,$select, "REFU.GetStringParameter 43\n");  #serial


updateUSS($socket,$select, 2000,0, PWD_DEVELOPMENT );
ping($socket,$select);
#sendRTP($socket,$select, "REFU.SetStringParameter 20,0,\"802R020\"\n");  





sendRTP($socket,$select, "REFU.GetStringParameter 0\n");  #full version
sendRTP($socket,$select, "REFU.GetFirmwareVersion\n"); 
sendRTP($socket,$select, "REFU.GetFirmwareBuild\n"); 



#sendRTP($socket,$select, "REFU.PORTAL_Testfunktion\n");

#"REFU.PORTAL_CommitPortalData",
#"REFU.PORTAL_GetFlash",
#"REFU.PORTAL_GetPortalData",
#"REFU.PORTAL_PortalFalsh_KillFutureTimes",
#"REFU.PORTAL_PortalFlash_KillAllPages",
#"REFU.PORTAL_SetFlash",
#"REFU.PORTAL_Testfunktion",
#PORTAL_INTERVAL => { cmd=>470, id=>0, type=>LONG, digits=>0, updatefreq=>LONG, comment=>'Sendeintervall des Portals', unit=>'m', min=>1, max=>16000, default=>10 }, 

#sendRTP($socket,$select, "REFU.PORTAL_GetPortalData\n");

#LOGGER_ENABLE   => { cmd=>450, id=>0, type=>LONG, digits=>0, updatefreq=>LONG, comment=>'Datenlogger', unit=>'0=aus/1=an' },
#LOGGER_INTERVAL => { cmd=>451, id=>0, type=>LONG, digits=>0, updatefreq=>LONG, comment=>'Datenlogger-Intervall', unit=>'s' }, # U16 ?   30/300/600
#
#LOGGER_PARAMETER_0  => { cmd=>452, id=>0,  type=>LONG, digits=>0, updatefreq=>LONG, comment=>'Datenlogger Parameter 0' },
#LOGGER_INDEX_0      => { cmd=>453, id=>0,  type=>LONG, digits=>0, updatefreq=>LONG, comment=>'Datenlogger Index 0' },
#LOGGER_PARAMETER_39 => { cmd=>452, id=>39, type=>LONG, digits=>0, updatefreq=>LONG, comment=>'Datenlogger Parameter 0' },
#LOGGER_INDEX_39     => { cmd=>453, id=>39, type=>LONG, digits=>0, updatefreq=>LONG, comment=>'Datenlogger Index 0' },

#UNKNOWN_454 => { cmd=>454, id=>0, type=>DEBUG, 
#		paraminfo=>'<answer type="ok"><min>0</min><max>100</max><default>0</default><unit>0</unit><decimal>0</decimal><type>517</type><arraySize>1</arraySize><flags>257</flags><check>32775</check><name>Datenlogger Zugriffsschalter</name></answer>' },

# logger an/aus
#requestUSS($socket,$select, 450,0 );
# logger interval
#requestUSS($socket,$select, 451,0 );

# logger paramtere/index
#requestUSS($socket,$select, 452,0 );
#requestUSS($socket,$select, 453,0 );
#requestUSS($socket,$select, 452,1 );
#requestUSS($socket,$select, 453,1 );
#requestUSS($socket,$select, 452,2 );
#requestUSS($socket,$select, 453,2 );
#requestUSS($socket,$select, 452,39 );
#requestUSS($socket,$select, 453,39 );

# logger zugriffsschalter		
#requestUSS($socket,$select, 454,0 );

#"REFU.BF_Basisbild2",
#"REFU.BF_GetBasisbildanzahl",
#"REFU.BF_GetDiagramm",
#"REFU.DATLOG_Analyse",
#"REFU.DATLOG_Format",
#"REFU.DATLOG_GetData",
#"REFU.DATLOG_KillFutureTimes",
#"REFU.DATLOG_QuickFormat",
#"REFU.DATLOG_RingLogAnalyse",
#"REFU.DATLOG_RingLog_Format",
#"REFU.DATLOG_RingLog_QuickFormat",
#"REFU.DATLOG_StopWatchdogFeed",

#sendRTP($socket,$select, "REFU.DATLOG_Analyse\n");  
#sendRTP($socket,$select, "REFU.DATLOG_GetData\n");  
#sendRTP($socket,$select, "REFU.DATLOG_GetData \"01.09.2013 16:10:00\",\"04.09.2013 16:20:00\"\n");  
#sendRTP($socket,$select, "REFU.DATLOG_GetData \"01.09.2013 00:00:00\",\"04.09.2013 00:00:00\"\n");  
#sendRTP($socket,$select, "REFU.DATLOG_GetData \"08.12.2016 11:00:00\",\"08.12.2016 11:10:00\"\n");  
#sendRTP($socket,$select, "REFU.DATLOG_GetData \"08.12.2016 11:00:00\",\"08.12.2016 11:10:00\",{1106,1123}\n");  

#sendRTP($socket,$select, 'REFU.DATLOG_GetData "08.12.2016 11:00:00","08.12.2016 11:10:00",{1106,1123,1124,1122,1107,1104,1105,92,'.(1*65536+92).',1191,1193,1150,501,1151,1152,'.(2*65536+92).','.(3*65536+92).',1156,1162,'.(1*65536+1123).','.(2*65536+1123).','.(3*65536+1123).'}'."\n");  
#sendRTP($socket,$select, 'REFU.DATLOG_GetData "08.12.2016 11:00:00","08.12.2016 11:10:00",{'.(1*65536+92).',1191,1193,1150,501,1151,1152,'.(2*65536+92).','.(3*65536+92).',1156,1162,'.(1*65536+1123).','.(2*65536+1123).','.(3*65536+1123).'}'."\n");  


#        0x0020:  5018 40e8 4501 0000 5245 4655 2e44 4154  P.@.E...REFU.DAT
#        0x0030:  4c4f 475f 4765 7444 6174 6120 3133 3739  LOG_GetData.1379
#        0x0040:  3238 3936 3030 2c31 3438 3133 3238 3030  289600,148132800
#        0x0050:  302c 7b31 3130 367d 0a                   0,{1106}.

		
		
#sendRTP($socket,$select, "REFU.DATLOG_RingLog\n");  # ???

#GetLastErrors =>	{ special=>0x80, cmd=>0x17, id=>0x30, type=>HASH, updatefreq=>FIX, command=>'REFU.ERROR_GetLastErrors\n', comment=>'Letzte Fehler' }, 
# {{2148139274,1410424779,"Netzunterspannung LT",6,515,0,0,0,0,0,0},{2148139030,1410424778,"Unterfrequenz",6,514,0,0,0,0,0,0}}

#"REFU.ERROR_ClearErrorBuffer",
#"REFU.ERROR_GetFehlerText",
#"REFU.ERROR_GetUSSFehlertext",
#"REFU.ERROR_KillFutureTimes",

#sendRTP($socket,$select, "REFU.ERROR_GetLastErrors\n");

		
## sendeinterval
#requestUSS($socket,$select, 470,0 );

## host, vorher url
#sendRTP($socket,$select, "REFU.GetStringParameter 471\n");  


## konfigversand
#requestUSS($socket,$select, 472,0 );

## portalaktivierung
#requestUSS($socket,$select, 473,0 );


## ip
#requestUSS($socket,$select, 474,0 );
#requestUSS($socket,$select, 474,1 );
#requestUSS($socket,$select, 474,2 );
#requestUSS($socket,$select, 474,3 );

## port
#requestUSS($socket,$select, 475,0 );

## portalstatus
#requestUSS($socket,$select, 476,0 );

## command request enable
#requestUSS($socket,$select, 477,0 );
## command request interval
#requestUSS($socket,$select, 478,0 );
## URI
#sendRTP($socket,$select, "REFU.GetStringParameter 479\n"); 

#sendRTP($socket,$select, "REFU.PORTAL_Testfunktion\n");


#sendRTP($socket,$select, "REFU.PORTAL_GetFlash 0\n"); #  # nutzdaten
#sendRTP($socket,$select, "REFU.PORTAL_GetFlash 1\n"); #  # fehlerdaten






#ping($socket,$select);
#updateUSS($socket,$select, 2000,0, PWD_USER );
#ping($socket,$select);
#updateUSS($socket,$select, 472,0, 1 );
#ping($socket,$select);
#requestUSS($socket,$select, 472,0 );



ping($socket,$select);
updateUSS($socket,$select, 2000,0, PWD_USER );
#ping($socket,$select);
#updateUSS($socket,$select, 2000,0, PWD_DEVELOPMENT );
#ping($socket,$select);
#updateUSS($socket,$select, 474,0, 88 );
#ping($socket,$select);
#updateUSS($socket,$select, 474,1, 99 );
#ping($socket,$select);
#updateUSS($socket,$select, 474,2, 57 );
#ping($socket,$select);
#updateUSS($socket,$select, 474,3, 184 );
#ping($socket,$select);
#updateUSS($socket,$select, 475,0, 8830 );
#ping($socket,$select);
#sendRTP($socket,$select, "REFU.SetStringParameter 471,0,\"88.99.57.184\"\n");  
#sendRTP($socket,$select, "REFU.SetStringParameter 471,0,\"is.refulog.com\"\n");  
#sendRTP($socket,$select, "REFU.SetStringParameter 471,0,\"static.184.57.99.88.clients.your-server.de\"\n");  
#sendRTP($socket,$select, "REFU.SetStringParameter 471,0,\"www.netadair.de\"\n");  
ping($socket,$select);

#sendRTP($socket,$select, "REFU.PORTAL_Testfunktion\n");


# PAC-Limit
requestUSS($socket,$select, 1163,0 );

#ping($socket,$select);
#updateUSS($socket,$select, 1163,0, 100 );
updateUSS($socket,$select, 1163,0, 55 );
ping($socket,$select);
requestUSS($socket,$select, 1163,0 );



#ping($socket,$select);
#sendRTP($socket,$select, "REFU.PORTAL_PortalFlash_KillAllPages\n");
#ping($socket,$select);



#UNKNOWN_471 => { cmd=>471, id=>0, type=>DEBUG, 
#		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>517</type><arraySize>70</arraySize><flags>278</flags><check>32775</check><name>URL</name></answer>' },
#UNKNOWN_472 => { cmd=>472, id=>0, type=>DEBUG, 
#		paraminfo=>'<answer type="ok"><min>0</min><max>1</max><default>0</default><unit>0</unit><decimal>0</decimal><type>517</type><arraySize>1</arraySize><flags>273</flags><check>32775</check><name>Konfigversendung</name></answer>' },
#UNKNOWN_473 => { cmd=>473, id=>0, type=>DEBUG, 
#		paraminfo=>'<answer type="ok"><min>0</min><max>1</max><default>0</default><unit>0</unit><decimal>0</decimal><type>517</type><arraySize>1</arraySize><flags>17</flags><check>32775</check><name>Aktivierung des Portals</name></answer>' },

#UNKNOWN_474 => { cmd=>474, id=>0, type=>DEBUG, 
#		paraminfo=>'<answer type="ok"><min>0</min><max>255</max><default>0</default><unit>0</unit><decimal>0</decimal><type>517</type><arraySize>4</arraySize><flags>22</flags><check>32775</check><name>IP-Adresse des Webportals</name></answer>' },
#UNKNOWN_475 => { cmd=>475, id=>0, type=>DEBUG, 
#		paraminfo=>'<answer type="ok"><min>0</min><max>65535</max><default>0</default><unit>0</unit><decimal>0</decimal><type>1030</type><arraySize>1</arraySize><flags>22</flags><check>32775</check><name>Port des Webportals</name></answer>' },

#UNKNOWN_476 => { cmd=>476, id=>0, type=>DEBUG, 
#		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>517</type><arraySize>1</arraySize><flags>256</flags><check>32768</check><name>Portal_State</name></answer>' },

#UNKNOWN_477 => { cmd=>477, id=>0, type=>DEBUG, 
#		paraminfo=>'<answer type="ok"><min>0</min><max>1</max><default>0</default><unit>0</unit><decimal>0</decimal><type>517</type><arraySize>1</arraySize><flags>1</flags><check>32775</check><name>CommandRequestAktivierung</name></answer>' },
#UNKNOWN_478 => { cmd=>478, id=>0, type=>DEBUG, 
#		paraminfo=>'<answer type="ok"><min>1</min><max>65535</max><default>720</default><unit>17924</unit><decimal>0</decimal><type>1030</type><arraySize>1</arraySize><flags>17</flags><check>32775</check><name>Intervall des Commandrequests</name></answer>' },
#UNKNOWN_479 => { cmd=>479, id=>0, type=>DEBUG, 
#		paraminfo=>'<answer type="ok"><unit>0</unit><decimal>0</decimal><type>517</type><arraySize>100</arraySize><flags>278</flags><check>32775</check><name>Portal URI</name></answer>' },
#



#updateUSS($socket,$select, 2000,0, PWD_USER );
#updateUSS($socket,$select, 414,3, 7 );

# PAC limnit 10%
####
#requestUSS($socket,$select, 1163,0 );
#requestUSS($socket,$select, 1162,0 );
#ping($socket,$select);
#updateUSS($socket,$select, 1162,0, 1000 );
#updateUSS($socket,$select, 1162,0, 50 );
#updateUSS($socket,$select, 1163,0, 5 );
#updateUSS($socket,$select, 1163,0, 2 );

####
#updateUSS($socket,$select, 1163,0, 40 );
#ping($socket,$select);
#requestUSS($socket,$select, 1162,0 );
#requestUSS($socket,$select, 1163,0 );


#requestUSS($socket,$select, 33,0 );
#requestUSS($socket,$select, 1137,0 );
#requestUSS($socket,$select, 1138,0 );
#requestUSS($socket,$select, 1161,0 );


#updateUSS($socket,$select, 2000,0, PWD_LIMIT );
#updateUSS($socket,$select, 1162,0, 1000 );
#requestUSS($socket,$select, 1162,0 );


#dev cc cc2 works!

#updateUSS($socket,$select, 2000,0, PWD_DEVELOPMENT );

#updateUSS($socket,$select, 2000,0, PWD_SPCOUNTRYCODE );
#updateUSS($socket,$select, 2000,0, PWD_SPCOUNTRYCODE_2 );

#updateUSS($socket,$select, 2000,0, PWD_SPCOUNTRYCODE_3 );

#updateUSS($socket,$select, 2000,0, PWD_SPCOUNTRYSETTINGS );
#updateUSS($socket,$select, 2000,0, PWD_SPCOUNTRYSETTINGS_2 );
#updateUSS($socket,$select, 2000,0, PWD_SPCOUNTRYSETTINGS_3 );

ping($socket,$select);

#foreach my $code ( PWD_DEVELOPMENT, PWD_SPCOUNTRYCODE, PWD_SPCOUNTRYCODE_2, PWD_SPCOUNTRYCODE_3, PWD_SPCOUNTRYSETTINGS, PWD_SPCOUNTRYSETTINGS_2, PWD_SPCOUNTRYSETTINGS_3 )
#foreach my $code ( PWD_DEBUG, PWD_PRODUKTION, PWD_DEVELOPMENT, PWD_SPCOUNTRYCODE, PWD_SPCOUNTRYCODE_2, PWD_SPCOUNTRYCODE_3, PWD_SPCOUNTRYSETTINGS, PWD_SPCOUNTRYSETTINGS_2, PWD_SPCOUNTRYSETTINGS_3 )
#{
#updateUSS($socket,$select, 2000,0, $code );

#updateUSS($socket,$select, 2000,0, 0 );
#requestUSS($socket,$select, 2001,0 );

#sendRTP($socket,$select, "REFU.GetLaendercodeListe\n");

#sendRTP($socket,$select, "REFU.GLOBPPC_Reboot\n");
#requestUSS($socket,$select, 2001,0 );


# 25.x: RTP answer: {{0,"Kein Land",0,0},{1,"Belgie",32,0},{2,"esko",420,0},{3,"Deutschland",49,0},{4,"Españ34,0},{5,"France",33,0},{6,"Greece (Continent)",30,0},{7,"Greek Islands",30,1},{8,"Italia",39,0},{9,"Italien Option",39,1},{10,"South Korea kepco/UL",82,0},{11,"South Korea ks pv501",82,1},{12,"Slovenija",386,0}}


#sendRTP($socket,$select, "REFU.PARAM_GetNummernListe\n");

# alt!!!!!
#sendRTP($socket,$select, "REFU.GetCommandList");

#sendRTP($socket,$select, "REFU.GLOBPBC_SetCountryCode 49,0");

#updateUSS($socket,$select, 34,0, 49 );

#requestUSS($socket,$select, 34,0 );
#requestUSS($socket,$select, 34,1 );
#sendRTP($socket,$select, "REFU.GetLaendercode");
#sendRTP($socket,$select, "REFU.GetLaenderGrenzwerte");

#}

#foreach my $params25 ( @{ parserefuanswer_liste('{0,1,3,5,20,21,22,23,24,26,27,28,30,31,33,34,35,36,37,39,40,42,43,44,45,46,47,48,81,82,83,85,86,88,90,92,93,94,95,96,98,200,201,220,221,222,223,224,225,226,227,251,252,253,254,255,256,257,261,262,263,264,265,266,267,400,401,402,403,404,405,406,407,410,411,412,413,414,415,420,421,422,423,450,451,452,453,470,471,472,473,474,475,476,477,490,500,501,502,503,504,505,600,601,602,801,802,810,900,901,902,903,904,905,906,907,908,909,910,1100,1101,1102,1103,1104,1105,1106,1107,1108,1111,1120,1121,1122,1123,1124,1128,1129,1130,1132,1133,1134,1135,1136,1137,1138,1139,1140,1141,1142,1150,1151,1152,1153,1154,1155,1161,1162,1170,1171,1172,1173,1174,1175,1176,1177,1178,1179,1182,1183,1184,1185,1190,1191,1192,1193,2000,2001}') }
#)  {
#
##sendRTP($socket,$select, "REFU.PARAM_GetParameterInfo ${params25}");
#print "$params25 "; sendRTP($socket,$select, "REFU.PARAM_GetName ${params25}");
#}


## hat mit 29.6 funktioniert
#updateUSS($socket,$select, 2000,0, PWD_SPCOUNTRYCODE );
#ping($socket,$select);
#requestUSS($socket,$select, 150,0 );
#ping($socket,$select);
#updateUSS($socket,$select, 150,0, 3 );
#ping($socket,$select);
#requestUSS($socket,$select, 150,0 );



#requestUSS($socket,$select, 150,0 );
#ping($socket,$select);

#updateUSS($socket,$select, 150,0, 3 );
#ping($socket,$select);

#sendRTP($socket,$select, "REFU.GLOBPBC_SetCountryCode 3,0\n");

#requestUSS($socket,$select, 150,0 );




#ping($socket,$select);
#requestUSS($socket,$select, 180,0 );
#ping($socket,$select);
#updateUSS($socket,$select, 180,0, 180000 );
#ping($socket,$select);
#requestUSS($socket,$select, 180,0 );


#sendRTP($socket,$select, "REFU.GetTime\n");
#ping($socket,$select);
#sendRTP($socket,$select, strftime('REFU.SetTime "%d.%m.%Y %H:%M:%S"', localtime(time) ) );
#ping($socket,$select);
#sendRTP($socket,$select, "REFU.GetTime\n");


#requestUSS($socket,$select, 40,0 );
#ping($socket,$select);
#updateUSS($socket,$select, 40,0, 1400 );
#ping($socket,$select);
#requestUSS($socket,$select, 40,0 );


#sendRTP($socket,$select, "REFU.SetCountryDefaultValues");




# sendRTP($socket,$select, "REFU.PARAM_Save_SR_Parameter\n");

#requestUSS($socket,$select, 112,0 );


#updateUSS($socket,$select, 410,0, 192 );
#updateUSS($socket,$select, 410,1, 168 );
#updateUSS($socket,$select, 410,2, 1 );
#updateUSS($socket,$select, 410,3, 125 );
#sendRTP($socket,$select, "REFU.GLOBPPC_Reboot\n");



#for $cnt ( 0 .. 65535 ) {
#        my $memaddr=-$cnt*4;
#
#        printf "Addr: %8x ", $memaddr;
#        sendRTP($socket,$select, "REFU.GLOBPPC_ReadMem ${memaddr}\n");
#}

   #  sendRTP($socket,$select, "REFU.GLOBPPC_ReadMem -8\n");


#sendRTP($socket,$select, "REFU.FILES_GetFlashSize");
#
##for $cnt ( 0x180000/0x80 .. 0x180000/0x80*8-1) {
#for $cnt ( 0xc00000/0x80 .. 0xd00000/0x80-1) {
#for $cnt ( 0xe00000/0x80 .. 0xf00000/0x80-1) {
#for $cnt ( 0xf00000/0x80 .. 0x1000000/0x80-1) {
#for $cnt ( 0x200000/0x80 .. 0x220000/0x80-1) {
#for $cnt ( 0x220000/0x80 .. 0x240000/0x80-1) {

#for $cnt ( 0xc40000/0x80 .. 0xc50000/0x80-1) {
#        my $memaddr=$cnt*0x80;
#
#        printf "Addr: %8x ", $memaddr;
#        sendRTP($socket,$select, "REFU.FILES_GetFlash ${memaddr}\n");
#}



#for $cnt ( 0x000000/0x80/1024 .. 0x1000000/0x80/1024-1) {
#        my $memaddr=$cnt*0x80*1024;
#
#        printf "Addr: %8x ", $memaddr;
#        sendRTP($socket,$select, "REFU.FILES_GetFlash ${memaddr}\n");
#}








$socket->close();


