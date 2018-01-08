########	Constants Start	########

NEW_LU= 'LU_Type'
Desc = 'Descriptio'
TEX = 'TEXTURE'
Depth = 'DEPTH'
MONSOON_END_INDEX = 182

########	Constants End	########



########	Lookup Dictionaries Start	########

#Dictionary for generic land use types:
dict_lulc = {
	'forest-forest blank':'scrub forest',
	'forest-deciduous (dry/moist/thorn)-open': 'deciduous open',
	'agricultural land-crop land-rabi crop': 'agriculture',
	'forest-scrub forest': 'scrub forest',	
	'agricultural land-crop land-kharif crop': 'agriculture',
	'agricultural land-fallow-current fallow': 'fallow land',
	'wastelands-scrub land-open scrub': 'scrub open',
	'wastelands-gullied/ravinous land-gullied': 'scrub open',
	'forest-deciduous (dry/moist/thorn)-dense/closed': 'deciduous - dense',
	'wastelands-scrub land-dense scrub': 'scrub dense',
	'built up-built up (rural)-built up area (rural)': 'habitation',
	'waterbodies-reservoir/tanks-dry-zaid extent': 'water',
	'waterbodies-reservoir/tanks-dry-rabi extent': 'water',
	'agricultural land-crop land-zaid crop': 'agriculture',
	'waterbodies-reservoir/tanks-dry-kharif extent': 'water',
	'waterbodies-canal/drain-lined': 'water',
	'agricultural land-crop land-two crop area': 'agriculture',
	'built up-built up (urban)-vegetated area': 'habitation',
	'wastelands-barren rocky/stony waste': 'scrub dense',
	'agricultural land-plantation-agriculture plantation': 'agriculture',
	'agricultural land-crop land-more than two crop': 'agriculture',
	'waterbodies-river/stream-perennial': 'water',
	'built up-built up (urban)-transportation': 'habitation',
	'built up-built up (urban)-recreational':'habitation',
	'built up-built up (urban)-residential': 'habitation'
}

#Lookup for properties of various soils
dict_SoilProperties = {
	'soil type': (
		'HSG',
		'Sand %',
		'Clay %',
		'Gravel %',
		'WP',
		'FC',
		'Saturation',
		'Ksat mm/hr',
		'Bulk Density',
		'AWC'
	),
	'clay loam': ('D', 32, 34, 0, 0.206, 0.341, 0.442, 2.7, 1.48, 0.14),
	'clayey': ('D', 28, 51, 0, 0.303, 0.427, 0.487, 0.52, 1.36, 0.12),
	'gravelly clay': ('D', 23, 48, 10, 0.285, 0.415, 0.488, 0.83, 1.36, 0.12),
	'gravelly clay loam': ('D', 31, 34, 10, 0.206, 0.343, 0.444, 2.32, 1.47, 0.12),
	'gravelly loam': ('B', 41, 17, 10, 0.109, 0.0244, 0.408, 10.83, 1.57, 0.12),
	'gravelly sandy clay loam': ('B', 49, 26, 10, 0.16, 0.273, 0.412, 5.83, 1.56, 0.1),
	'gravelly sandy loam': ('B', 63, 10, 10, 0.065, 0.158, 0.402, 33.29, 1.58, 0.08),
	'gravelly silty clay': ('C', 7, 47, 10, 0.277, 0.42, 0.512, 1.7, 1.29, 0.13),
	'gravelly silty loam': ('C', 21, 15, 10, 0.099, 0.282, 0.415, 6.8, 1.55, 0.16),
	'loamy': ('B', 42, 20, 0, 0.126, 0.256, 0.411, 10.2, 1.56, 0.13),
	'loamy sand': ('A', 82, 8, 0, 0.05, 0.106, 0.41, 69.09, 1.56, 0.06),
	'sandy': ('A', 91, 5, 0, 0.03, 0.071, 0.424, 108.06, 1.53, 0.04),
	'sandy clay': ('D', 51, 42, 0, 0.254, 0.364, 0.43, 0.73, 1.51, 0.11),
	'sandy clay loam': ('C', 57, 28, 0, 0.172, 0.271, 0.406, 6.09, 1.57, 0.1),
	'sandy loam': ('A', 65, 11, 0, 0.172, 0.258, 0.399, 6.67, 1.59, 0.09),
	'silty clay': ('D', 9, 46, 0, 0.272, 0.415, 0.506, 1.9, 1.31, 0.14),
	'silty clay loam': ('D', 11, 34, 0, 0.206, 0.371, 0.47, 2.65, 1.41, 0.17),
	'silty loam': ('B', 19, 16, 0, 0.105, 0.291, 0.418, 6.97, 1.54, 0.19),
	'waterbody mask': ('D', 28, 51, 0, 0.303, 0.427, 0.487, 0.52, 1.36, 0.12),
	'habitation mask': ('D', 32, 34, 0, 0.206, 0.341, 0.442, 2.7, 1.48, 0.14)
}

#Lookup for SCS curve no based on land ussage and HSG: 
dict_RO = {
	'agriculture': {'A': 67, 'B': 78, 'C': 85, 'D': 89},
	'deciduous - dense': {'A': 30, 'B': 55, 'C': 70, 'D': 77},
	'deciduous open': {'A': 36, 'B': 60, 'C': 73, 'D': 79},
	'fallow land': {'A': 77, 'B': 86, 'C': 91, 'D': 94},
	'habitation': {'A': 77, 'B': 85, 'C': 90, 'D': 92},
	'scrub dense': {'A': 49, 'B': 69, 'C': 79, 'D': 84},
	'scrub forest': {'A': 57, 'B': 73, 'C': 82, 'D': 86},
	'scrub open': {'A': 68, 'B': 79, 'C': 86, 'D': 89},
	'water': {'A': 100, 'B': 100, 'C': 100, 'D': 100}
}

#Lookup for Soil depth with respect to given soil depth in Soil map: 
dict_SoilDep = {
	'deep (50 to 100 cm)': 1,
	'habitation mask': 0.1,
	'shallow (10 to 25 cm)': 0.25,
	'very deep (> 100 cm)': 1.5,
	'waterbody mask': 0.1,
	'moderately deep (25 to 50 cm)': 0.5,
	'shallow to very shallow (< 25 cm)': 0.25,
	'very shallow (< 10 cm)': 0.1
}

#Lookup for Crop properties : KC, depletion factor, root depth
dict_crop = {
	'soyabean':		(	[0.3]*20 + [0.7]*25 + [1.15]*45 + [0.7]*20,		0.5,	0.9		),
	'bajra':		(	[0.7]*15 + [1]*25 + [0.3]*40 + [1.5]*25,		0.55,	1.5		),
	'moong':		(	[0.5]*20 + [1.15]*30 + [1.1]*35 + [0.5]*15,		0.45,	0.75	),
	'sorghum':		(	[0.53]*20 + [0.82]*35 + [1.24]*45 + [0.85]*30,	0.55,	1.5		),
	'cotton':		(	[0.45]*45 + [0.75]*90 + [1.15]*45 + [0.75]*45,	0.65,	1.35	),
	'udid':			(	[0.5]*20 + [1.15]*30 + [0.35]*35 + [0.4]*15,	0.45,	0.75	),
	'orange':		(	[0.8]*60 + [0.8]*90 + [0.8]*120 + [3]*95,		0.5,	1.1		),
	'rice':			(	[1.15]*30 + [1.23]*30 + [1.14]*80 + [1.02]*40,	0.2,	0.75	),
	'sunflower':	(	[0.63]*25 + [0.82]*35 + [1.12]*45 + [1.23]*25,	0.45,	1.15	),
	'tur':			(	[0.45]*20 + [0.85]*30 + [1.15]*35 + [1.05]*15,	0.45,	0.75	),
	'grapes':		(	[0.3]*20 + [0.7]*40 + [1.15]*120 + [2]*60,		0.5,	0.9		),
	'maize':		(	[0.55]*20 + [1]*35 + [1.23]*40 + [0.67]*30,		0.55,	1.35	)
}

#Lookup for properties of vegetation on various LULC types : KC, depletion factor, root depth
#	'deciduous open', 'scrub dense' and 'scrub forest' have been pooled together as 'Scrub Forest'
dict_LULC_pseudo_crop =	{
	'deciduous - dense':	(	[0.3]*45 + [1.15]*60 + [0.7]*90 + [0.1]*170,	0.8,	3	),
	'deciduous open':		(	[0.3]*30 + [0.7]*60 + [0.5]*60 + [0.2]*215,		0.6,	1.5	),
	'scrub dense':			(	[0.3]*30 + [0.7]*60 + [0.5]*60 + [0.2]*215,		0.6,	1.5	),
	'scrub open':			(	[0.5]*120 + [0.25]*60 + [0.15]*120 + [0.1]*65,	0.5,	0.5	),
	'scrub forest':			(	[0.3]*30 + [0.7]*60 + [0.5]*60 + [0.2]*215,		0.6,	1.5	)
}


#Long Kharif crops list
long_kharif_crops = ['cotton','orange','grapes','tur']

########	Lookup Dictionaries End		########
