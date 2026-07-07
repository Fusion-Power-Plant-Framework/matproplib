# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: LGPL-2.1-or-later

"""matproplib matml enums"""

from enum import Enum


class UncertaintyScale(Enum):
    """Uncertainty scales"""

    LINEAR = "Linear"
    LOGARITHMIC = "Logarithmic"


class DataFormat(Enum):
    """
    Possible data formats

    Notes
    -----
    "mixed" indicates that the not all of the parameter values are of the same
    type (e.g. a "No Break" value for an otherwise numeric set of Charpy
    Izod test results).
    """

    FLOAT = "float"
    INTEGER = "integer"
    STRING = "string"
    EXPONENTIAL = "exponential"
    MIXED = "mixed"


class ChemicalElementSymbol(Enum):
    """
    Valid strings representing chemical
    elements, which may be used in the Symbol element.

    :cvar H: Hydrogen
    :cvar HE: Helium
    :cvar LI: Lithium
    :cvar BE: Beryllium
    :cvar B: Boron
    :cvar C: Carbon
    :cvar N: Nitrogen
    :cvar O: Oxygen
    :cvar F: Fluorine
    :cvar NE: Neon
    :cvar NA: Sodium
    :cvar MG: Magnesium
    :cvar AL: Aluminium
    :cvar SI: Silicon
    :cvar P: Phosphorus
    :cvar S: Sulfur
    :cvar CL: Chlorine
    :cvar AR: Argon
    :cvar K: Potassium
    :cvar CA: Calcium
    :cvar SC: Scandium
    :cvar TI: Titanium
    :cvar V: Vanadium
    :cvar CR: Chromium
    :cvar MN: Manganese
    :cvar FE: Iron
    :cvar CO: Cobalt
    :cvar NI: Nickel
    :cvar CU: Copper
    :cvar ZN: Zinc
    :cvar GA: Gallium
    :cvar GE: Germanium
    :cvar AS: Arsenic
    :cvar SE: Selenium
    :cvar BR: Bromine
    :cvar KR: Krypton
    :cvar RB: Rubidium
    :cvar SR: Strontium
    :cvar Y: Yttrium
    :cvar ZR: Zirconium
    :cvar NB: Niobium
    :cvar MO: Molybdenum
    :cvar TC: Technetium
    :cvar RU: Ruthenium
    :cvar RH: Rhodium
    :cvar PD: Palladium
    :cvar AG: Silver
    :cvar CD: Cadmium
    :cvar IN: Indium
    :cvar SN: Tin
    :cvar SB: Antimony
    :cvar TE: Tellurium
    :cvar I: Iodine
    :cvar XE: Xenon
    :cvar CS: Caesium
    :cvar BA: Barium
    :cvar LA: Lanthanum
    :cvar CE: Cerium
    :cvar PR: Praseodymium
    :cvar ND: Neodymium
    :cvar PM: Promethium
    :cvar SM: Samarium
    :cvar EU: Europium
    :cvar GD: Gadolinium
    :cvar TB: Terbium
    :cvar DY: Dysprosium
    :cvar HO: Holmium
    :cvar ER: Erbium
    :cvar TM: Thulium
    :cvar YB: Ytterbium
    :cvar LU: Lutetium
    :cvar HF: Hafnium
    :cvar TA: Tantalum
    :cvar W: Tungsten
    :cvar RE: Rhenium
    :cvar OS: Osmium
    :cvar IR: Iridium
    :cvar PT: Platinum
    :cvar AU: Gold
    :cvar HG: Mercury
    :cvar TL: Thallium
    :cvar PB: Lead
    :cvar BI: Bismuth
    :cvar PO: Polonium
    :cvar AT: Astatine
    :cvar RN: Radon
    :cvar FR: Francium
    :cvar RA: Radium
    :cvar AC: Actinium
    :cvar TH: Thorium
    :cvar PA: Protactinium
    :cvar U: Uranium
    :cvar NP: Neptunium
    :cvar PU: Plutonium
    :cvar AM: Americium
    :cvar CM: Curium
    :cvar BK: Berkelium
    :cvar CF: Californium
    :cvar ES: Einsteinium
    :cvar FM: Fermium
    :cvar MD: Mendelevium
    :cvar NO: Nobelium
    :cvar LR: Lawrencium
    :cvar RF: Rutherfordium
    :cvar DB: Dubnium
    :cvar SG: Seaborgium
    :cvar BH: Bohrium
    :cvar HS: Hassium
    :cvar MT: Meitnerium
    :cvar UUN: Ununnilium
    :cvar UUU: Unununium
    :cvar UUB: Ununbium
    :cvar UUQ: Ununquadium
    :cvar UUH: Ununhexium
    :cvar UUO: Ununoctium
    """

    H = "H"
    HE = "He"
    LI = "Li"
    BE = "Be"
    B = "B"
    C = "C"
    N = "N"
    O = "O"  # noqa: E741
    F = "F"
    NE = "Ne"
    NA = "Na"
    MG = "Mg"
    AL = "Al"
    SI = "Si"
    P = "P"
    S = "S"
    CL = "Cl"
    AR = "Ar"
    K = "K"
    CA = "Ca"
    SC = "Sc"
    TI = "Ti"
    V = "V"
    CR = "Cr"
    MN = "Mn"
    FE = "Fe"
    CO = "Co"
    NI = "Ni"
    CU = "Cu"
    ZN = "Zn"
    GA = "Ga"
    GE = "Ge"
    AS = "As"
    SE = "Se"
    BR = "Br"
    KR = "Kr"
    RB = "Rb"
    SR = "Sr"
    Y = "Y"
    ZR = "Zr"
    NB = "Nb"
    MO = "Mo"
    TC = "Tc"
    RU = "Ru"
    RH = "Rh"
    PD = "Pd"
    AG = "Ag"
    CD = "Cd"
    IN = "In"
    SN = "Sn"
    SB = "Sb"
    TE = "Te"
    I = "I"  # noqa: E741
    XE = "Xe"
    CS = "Cs"
    BA = "Ba"
    LA = "La"
    CE = "Ce"
    PR = "Pr"
    ND = "Nd"
    PM = "Pm"
    SM = "Sm"
    EU = "Eu"
    GD = "Gd"
    TB = "Tb"
    DY = "Dy"
    HO = "Ho"
    ER = "Er"
    TM = "Tm"
    YB = "Yb"
    LU = "Lu"
    HF = "Hf"
    TA = "Ta"
    W = "W"
    RE = "Re"
    OS = "Os"
    IR = "Ir"
    PT = "Pt"
    AU = "Au"
    HG = "Hg"
    TL = "Tl"
    PB = "Pb"
    BI = "Bi"
    PO = "Po"
    AT = "At"
    RN = "Rn"
    FR = "Fr"
    RA = "Ra"
    AC = "Ac"
    TH = "Th"
    PA = "Pa"
    U = "U"
    NP = "Np"
    PU = "Pu"
    AM = "Am"
    CM = "Cm"
    BK = "Bk"
    CF = "Cf"
    ES = "Es"
    FM = "Fm"
    MD = "Md"
    NO = "No"
    LR = "Lr"
    RF = "Rf"
    DB = "Db"
    SG = "Sg"
    BH = "Bh"
    HS = "Hs"
    MT = "Mt"
    UUN = "Uun"
    UUU = "Uuu"
    UUB = "Uub"
    UUQ = "Uuq"
    UUH = "Uuh"
    UUO = "Uuo"


class CurrencyCode(Enum):
    """*
    Based on ISO-4217, and taken from paper N699 on http://www.jtc1sc32.org/
    As of 2003-12-11 permission to use this element has been sought from, but
    not yet been granted by, the authors of the paper.
    This element declares the content model for value, which contains a string
    representing a currency.
    For the most current updates, refer to
    http://www.din.de/gremien/nas/nabd/iso4217ma/codlistp1/en_listp1.html.

    :cvar AFA: Afghani
    :cvar ALL: Lek
    :cvar AMD: Armenian Dram
    :cvar ANG: Netherlands Antillian Guilder
    :cvar AOA: Kwanza
    :cvar ARS: Argentine Peso
    :cvar ATS: Schilling
    :cvar AUD: Australian Dollar
    :cvar AWG: Aruban Guilder
    :cvar AZM: Azerbaijanian Manat
    :cvar BAM: Convertible Marks
    :cvar BBD: Barbados Dollar
    :cvar BDT: Taka
    :cvar BEF: Belgian Franc
    :cvar BGL: Lev
    :cvar BGN: Bulgarian Lev
    :cvar BHD: Bahraini Dinar
    :cvar BIF: Burundi Franc
    :cvar BMD: Bermudian Dollar
    :cvar BND: Brunei Dollar
    :cvar BOB: Boliviano
    :cvar BOV: Mvdol
    :cvar BRL: Brazilian Real
    :cvar BSD: Bahamian Dollar
    :cvar BTN: Ngultrum
    :cvar BWP: Pula
    :cvar BYB: Belarussian Ruble
    :cvar BYR: Belarussian Ruble
    :cvar BZD: Belize Dollar
    :cvar CAD: Canadian Dollar
    :cvar CDF: Franc Congolais
    :cvar CHF: Swiss Franc
    :cvar CLF: Unidades de fomento
    :cvar CLP: Chilean Peso
    :cvar CNY: Yuan Renminbi
    :cvar COP: Colombian Peso
    :cvar CRC: Costa Rican Colon
    :cvar CUP: Cuban Peso
    :cvar CVE: Cape Verde Escudo
    :cvar CYP: Cyprus Pound
    :cvar CZK: Czech Koruna
    :cvar DEM: Deutsche Mark
    :cvar DJF: Djibouti Franc
    :cvar DKK: Danish Krone
    :cvar DOP: Dominican Peso
    :cvar DZD: Algerian Dinar
    :cvar EEK: Kroon
    :cvar EGP: Egyptian Pound
    :cvar ERN: Nakfa
    :cvar ESP: Spanish Peseta
    :cvar ETB: Ethiopian Birr
    :cvar EUR: Euro
    :cvar FIM: Markka
    :cvar FJD: Fiji Dollar
    :cvar FKP: Falkland Islands Pound
    :cvar FRF: French Franc
    :cvar GBP: Pound Sterling
    :cvar GEL: Lari
    :cvar GHC: Cedi
    :cvar GIP: Gibraltar Pound
    :cvar GMD: Dalasi
    :cvar GNF: Guinea Franc
    :cvar GRD: Drachma
    :cvar GTQ: Quetzal
    :cvar GWP: Guinea-Bissau Peso
    :cvar GYD: Guyana Dollar
    :cvar HKD: Hong Kong Dollar
    :cvar HNL: Lempira
    :cvar HRK: Croatian kuna
    :cvar HTG: Gourde
    :cvar HUF: Forint
    :cvar IDR: Rupiah
    :cvar IEP: Irish Pound
    :cvar ILS: New Israeli Sheqel
    :cvar INR: Indian Rupee
    :cvar IQD: Iraqi Dinar
    :cvar IRR: Iranian Rial
    :cvar ISK: Iceland Krona
    :cvar ITL: Italian Lira
    :cvar JMD: Jamaican Dollar
    :cvar JOD: Jordanian Dinar
    :cvar JPY: Yen
    :cvar KES: Kenyan Shilling
    :cvar KGS: Som
    :cvar KHR: Riel
    :cvar KMF: Comoro Franc
    :cvar KPW: North Korean Won
    :cvar KRW: Won
    :cvar KWD: Kuwaiti Dinar
    :cvar KYD: Cayman Islands Dollar
    :cvar KZT: Tenge
    :cvar LAK: Kip
    :cvar LBP: Lebanese Pound
    :cvar LKR: Sri Lanka Rupee
    :cvar LRD: Liberian Dollar
    :cvar LSL: Loti
    :cvar LTL: Lithuanian Litus
    :cvar LUF: Luxembourg Franc
    :cvar LVL: Latvian Lats
    :cvar LYD: Libyan Dinar
    :cvar MAD: Moroccan Dirham
    :cvar MDL: Moldovan Leu
    :cvar MGF: Malagasy Franc
    :cvar MKD: Denar
    :cvar MMK: Kyat
    :cvar MNT: Tugrik
    :cvar MOP: Pataca
    :cvar MRO: Ouguiya
    :cvar MTL: Maltese Lira
    :cvar MUR: Mauritius Rupee
    :cvar MVR: Rufiyaa
    :cvar MWK: Kwacha
    :cvar MXN: Mexican Peso
    :cvar MXV: Mexican Unidad de Inversion (UDI)
    :cvar MYR: Malaysian Ringgit
    :cvar MZM: Metical
    :cvar NAD: Namibia Dollar
    :cvar NGN: Naira
    :cvar NIO: Cordoba Oro
    :cvar NLG: Netherlands Guilder
    :cvar NOK: Norwegian Krone
    :cvar NPR: Nepalese Rupee
    :cvar NZD: New Zealand Dollar
    :cvar OMR: Rial Omani
    :cvar PAB: Balboa
    :cvar PEN: Nuevo Sol
    :cvar PGK: Kina
    :cvar PHP: Philippine Peso
    :cvar PKR: Pakistan Rupee
    :cvar PLN: Zloty
    :cvar PTE: Portuguese Escudo
    :cvar PYG: Guarani
    :cvar QAR: Qatari Rial
    :cvar ROL: Leu
    :cvar RUB: Russian Ruble
    :cvar RUR: Russian Ruble
    :cvar RWF: Rwanda Franc
    :cvar SAR: Saudi Riyal
    :cvar SBD: Solomon Islands Dollar
    :cvar SCR: Seychelles Rupee
    :cvar SDD: Sudanese Dinar
    :cvar SEK: Swedish Krona
    :cvar SGD: Singapore Dollar
    :cvar SHP: Saint Helena Pound
    :cvar SIT: Tolar
    :cvar SKK: Slovak Koruna
    :cvar SLL: Leone
    :cvar SOS: Somali Shilling
    :cvar SRG: Suriname Guilder
    :cvar STD: Dobra
    :cvar SVC: El Salvador Colon
    :cvar SYP: Syrian Pound
    :cvar SZL: Lilangeni
    :cvar THB: Baht
    :cvar TJR: Tajik Ruble
    :cvar TMM: Manat
    :cvar TND: Tunisian Dinar
    :cvar TOP: Pa'anga
    :cvar TPE: Timor Escudo
    :cvar TRL: Turkish Lira
    :cvar TTD: Trinidad and Tobago Dollar
    :cvar TWD: New Taiwan Dollar
    :cvar TZS: Tanzanian Shilling
    :cvar UAH: Hryvnia
    :cvar UGX: Uganda Shilling
    :cvar USD: US Dollar
    :cvar UYU: Peso Uruguayo
    :cvar UZS: Uzbekistan Sum
    :cvar VEB: Bolivar
    :cvar VND: Dong
    :cvar VUV: Vatu
    :cvar WST: Tala
    :cvar XAF: CFA Franc BEAC
    :cvar XCD: East Caribbean Dollar
    :cvar XDR: SDR
    :cvar XOF: CFA Franc BCEAO
    :cvar XPF: CFP Franc
    :cvar YER: Yemeni Rial
    :cvar YUM: Yugoslavian Dinar
    :cvar ZAR: Rand
    :cvar ZMK: Kwacha
    :cvar ZWD: Zimbabwe Dollar
    """

    AFA = "AFA"
    ALL = "ALL"
    AMD = "AMD"
    ANG = "ANG"
    AOA = "AOA"
    ARS = "ARS"
    ATS = "ATS"
    AUD = "AUD"
    AWG = "AWG"
    AZM = "AZM"
    BAM = "BAM"
    BBD = "BBD"
    BDT = "BDT"
    BEF = "BEF"
    BGL = "BGL"
    BGN = "BGN"
    BHD = "BHD"
    BIF = "BIF"
    BMD = "BMD"
    BND = "BND"
    BOB = "BOB"
    BOV = "BOV"
    BRL = "BRL"
    BSD = "BSD"
    BTN = "BTN"
    BWP = "BWP"
    BYB = "BYB"
    BYR = "BYR"
    BZD = "BZD"
    CAD = "CAD"
    CDF = "CDF"
    CHF = "CHF"
    CLF = "CLF"
    CLP = "CLP"
    CNY = "CNY"
    COP = "COP"
    CRC = "CRC"
    CUP = "CUP"
    CVE = "CVE"
    CYP = "CYP"
    CZK = "CZK"
    DEM = "DEM"
    DJF = "DJF"
    DKK = "DKK"
    DOP = "DOP"
    DZD = "DZD"
    EEK = "EEK"
    EGP = "EGP"
    ERN = "ERN"
    ESP = "ESP"
    ETB = "ETB"
    EUR = "EUR"
    FIM = "FIM"
    FJD = "FJD"
    FKP = "FKP"
    FRF = "FRF"
    GBP = "GBP"
    GEL = "GEL"
    GHC = "GHC"
    GIP = "GIP"
    GMD = "GMD"
    GNF = "GNF"
    GRD = "GRD"
    GTQ = "GTQ"
    GWP = "GWP"
    GYD = "GYD"
    HKD = "HKD"
    HNL = "HNL"
    HRK = "HRK"
    HTG = "HTG"
    HUF = "HUF"
    IDR = "IDR"
    IEP = "IEP"
    ILS = "ILS"
    INR = "INR"
    IQD = "IQD"
    IRR = "IRR"
    ISK = "ISK"
    ITL = "ITL"
    JMD = "JMD"
    JOD = "JOD"
    JPY = "JPY"
    KES = "KES"
    KGS = "KGS"
    KHR = "KHR"
    KMF = "KMF"
    KPW = "KPW"
    KRW = "KRW"
    KWD = "KWD"
    KYD = "KYD"
    KZT = "KZT"
    LAK = "LAK"
    LBP = "LBP"
    LKR = "LKR"
    LRD = "LRD"
    LSL = "LSL"
    LTL = "LTL"
    LUF = "LUF"
    LVL = "LVL"
    LYD = "LYD"
    MAD = "MAD"
    MDL = "MDL"
    MGF = "MGF"
    MKD = "MKD"
    MMK = "MMK"
    MNT = "MNT"
    MOP = "MOP"
    MRO = "MRO"
    MTL = "MTL"
    MUR = "MUR"
    MVR = "MVR"
    MWK = "MWK"
    MXN = "MXN"
    MXV = "MXV"
    MYR = "MYR"
    MZM = "MZM"
    NAD = "NAD"
    NGN = "NGN"
    NIO = "NIO"
    NLG = "NLG"
    NOK = "NOK"
    NPR = "NPR"
    NZD = "NZD"
    OMR = "OMR"
    PAB = "PAB"
    PEN = "PEN"
    PGK = "PGK"
    PHP = "PHP"
    PKR = "PKR"
    PLN = "PLN"
    PTE = "PTE"
    PYG = "PYG"
    QAR = "QAR"
    ROL = "ROL"
    RUB = "RUB"
    RUR = "RUR"
    RWF = "RWF"
    SAR = "SAR"
    SBD = "SBD"
    SCR = "SCR"
    SDD = "SDD"
    SEK = "SEK"
    SGD = "SGD"
    SHP = "SHP"
    SIT = "SIT"
    SKK = "SKK"
    SLL = "SLL"
    SOS = "SOS"
    SRG = "SRG"
    STD = "STD"
    SVC = "SVC"
    SYP = "SYP"
    SZL = "SZL"
    THB = "THB"
    TJR = "TJR"
    TMM = "TMM"
    TND = "TND"
    TOP = "TOP"
    TPE = "TPE"
    TRL = "TRL"
    TTD = "TTD"
    TWD = "TWD"
    TZS = "TZS"
    UAH = "UAH"
    UGX = "UGX"
    USD = "USD"
    UYU = "UYU"
    UZS = "UZS"
    VEB = "VEB"
    VND = "VND"
    VUV = "VUV"
    WST = "WST"
    XAF = "XAF"
    XCD = "XCD"
    XDR = "XDR"
    XOF = "XOF"
    XPF = "XPF"
    YER = "YER"
    YUM = "YUM"
    ZAR = "ZAR"
    ZMK = "ZMK"
    ZWD = "ZWD"
