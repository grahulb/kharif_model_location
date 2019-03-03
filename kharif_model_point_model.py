from constants_dicts_lookups import *
from math import exp, log

class Budget:

	def __init__(self):
		self.sm, self.rain, self.runoff, self.infil, self.AET, self.GW_rech = [],[],[],[],[],[]

class Crop:
	def __init__(self, name, sowing_threshold):
		self.name = name
		self.sowing_threshold = sowing_threshold
		self.KC = dict_crop[self.name][0] if self.name in dict_crop.keys() else dict_LULC_pseudo_crop[self.name][0]
		self.end_date_index = len(self.KC) - 1
		self.PET = [];
	
	@property
	def root_depth(self):	return dict_crop[self.name][2] if self.name in dict_crop.keys() else dict_LULC_pseudo_crop[self.name][2]
	@property
	def depletion_factor(self):	return dict_crop[self.name][1] if self.name in dict_crop.keys() else dict_LULC_pseudo_crop[self.name][1]
	
	def calculate_PET(self, rain, et0, model_duration):
		def compute_sowing_index():
			if self.sowing_threshold == 0:  return 0
			rain_sum = 0
			for day in range (0,len(rain)):
				if (rain_sum < self.sowing_threshold):	rain_sum += rain[day]
				else :								    break
			return day
		kc = ([0]*compute_sowing_index()) + self.KC
		kc += [0]*(model_duration - len(kc))
		print len(et0), len(kc), model_duration
		self.PET = [et0[i]*kc[i]    for i in range(model_duration)]

class PointModel:
	
	def __init__(self, soil_texture, depth_value, lulc_type, slope, crop):
		self.soil_texture = soil_texture
		self.depth_value = depth_value
		self.lulc_type = lulc_type
		self.slope = slope
		self.crop = crop
		self.budget = Budget()
	
	@property
	def Ksat(self):	return dict_SoilProperties[self.soil_texture][7]
	@property
	def Sat(self):	return dict_SoilProperties[self.soil_texture][6]
	@property
	def WP(self):	return dict_SoilProperties[self.soil_texture][4]
	@property
	def FC(self):	return dict_SoilProperties[self.soil_texture][5]
	@property
	def HSG(self):	return dict_SoilProperties[self.soil_texture][0]
	@property
	def cn_val(self):	return dict_RO[self.lulc_type][self.HSG]
	
	def run_model(self, rain, model_duration):
		self.setup_for_daily_computations()
		self.SM1_fraction = self.layer2_moisture = self.WP
		
		for day in range(model_duration):
			self.primary_runoff(day, rain)
			self.aet(day, self.crop.PET)
			self.percolation_below_root_zone(day)
			self.secondary_runoff(day)
			self.percolation_to_GW(day)
		
	def setup_for_daily_computations(self):
		"""
		"""
		
		Sat_depth = self.Sat * self.depth_value * 1000
		self.WP_depth = self.WP * self.depth_value * 1000
		FC_depth = self.FC * self.depth_value * 1000
		if (self.depth_value <= self.crop.root_depth):  # thin soil layer
			self.SM1 = self.depth_value - 0.01
			self.SM2 = 0.01
		else:
			self.SM1 = self.crop.root_depth
			self.SM2 = self.depth_value - self.crop.root_depth
		
		cn_s = self.cn_val
		cn3 = cn_s * exp(0.00673 * (100 - cn_s))
		if (self.slope > 5.0):
			cn_s = (((cn3 - self.cn_val) / float(3)) * (1 - 2 * exp(-13.86 * self.slope * 0.01))) + self.cn_val
		cn1_s = cn_s - 20 * (100 - cn_s) / float(100 - cn_s + exp(2.533 - 0.0636 * (100 - cn_s)))
		cn3_s = cn_s * exp(0.00673 * (100 - cn_s))
		
		self.Smax = 25.4 * (1000 / float(cn1_s) - 10)
		S3 = 25.4 * (1000 / float(cn3_s) - 10)
		self.W2 = (log((FC_depth - self.WP_depth) / (1 - float(S3 / self.Smax)) - (FC_depth - self.WP_depth)) - log(
			(Sat_depth - self.WP_depth) / (1 - 2.54 / self.Smax) - (Sat_depth - self.WP_depth))) / (
				          (Sat_depth - self.WP_depth) - (FC_depth - self.WP_depth))
		self.W1 = log((FC_depth - self.WP_depth) / (1 - S3 / self.Smax) - (FC_depth - self.WP_depth)) + self.W2 * (
				FC_depth - self.WP_depth)
		
		TT_perc = (Sat_depth - FC_depth) / self.Ksat  # SWAT equation 2:3.2.4
		self.daily_perc_factor = 1 - exp(-24 / TT_perc)  # SWAT equation 2:3.2.3
	
	def primary_runoff(self, day, rain):
		"""
		Retention parameter 'S_swat' using SWAT equation 2:1.1.6
		Curve Number for the day 'Cn_swat' using SWAT equation 2:1.1.11
		Initial abstractions (surface storage,interception and infiltration prior to runoff)
			'Ia_swat' derived approximately as recommended by SWAT
		Primary Runoff 'Swat_RO' using SWAT equation 2:1.1.1
		"""
		self.budget.sm.append((self.SM1_fraction * self.SM1 + self.layer2_moisture * self.SM2) * 1000)
		# if not printed and self.sm[-1] > 100:    self.
		self.SW = self.budget.sm[-1] - self.WP_depth
		S_swat = self.Smax * (1 - self.SW / (self.SW + exp(self.W1 - self.W2 * self.SW)))
		
		Cn_swat = 25400 / float(S_swat + 254)
		Ia_swat = 0.2 * S_swat
		# ~ print 'len(rain), day : ', len(rain), day
		effective_rain = rain[day] + (0 if (day == 0 or self.budget.runoff[day-1] >= RUNOFF_THRESHOLD) else self.budget.runoff[day-1])
		self.budget.rain.append(effective_rain)
		if (effective_rain > Ia_swat):
			estimated_runoff = ((effective_rain - Ia_swat) ** 2) / (effective_rain + 0.8 * S_swat)
			self.budget.runoff.append(estimated_runoff if estimated_runoff > RUNOFF_THRESHOLD else 0)
		else:
			self.budget.runoff.append(0)
		self.budget.infil.append(rain[day] - self.budget.runoff[day])
		assert len(self.budget.runoff) == day + 1, (self.budget.runoff, day)
		assert len(self.budget.infil) == day + 1
	
	def aet(self, day, PET):
		"""
		Water Stress Coefficient 'KS' using FAO Irrigation and Drainage Paper 56, page 167 and
			page 169 equation 84
		Actual Evapotranspiration 'AET' using FAO Irrigation and Drainage Paper 56, page 6 and
			page 161 equation 81
		"""
		global printed
		if (self.SM1_fraction < self.WP):
			KS = 0
		elif (self.SM1_fraction > (self.FC * (1 - self.crop.depletion_factor) + self.crop.depletion_factor * self.WP)):
			KS = 1
		else:
			KS = (self.SM1_fraction - self.WP) / (self.FC - self.WP) / (1 - self.crop.depletion_factor)
		self.budget.AET.append(KS * PET[day])
	
	def percolation_below_root_zone(self, day):
		"""
		Calculate soil moisture (fraction) 'SM1_before' as the one after infiltration and (then) AET occur,
		but before percolation starts below root-zone. Percolation below root-zone starts only if
		'SM1_before' is more than field capacity and the soil below root-zone is not saturated,i.e.
		'layer2_moisture' is less than saturation. When precolation occurs it is derived as
		the minimum of the maximum possible percolation (using SWAT equation 2:3.2.3) and
		the amount available in the root-zone for percolation.
		"""
		self.SM1_before = (self.SM1_fraction * self.SM1 + (
				(self.budget.infil[day] - self.budget.AET[day]) / float(1000))) / self.SM1
		if (self.SM1_before < self.FC):
			self.R_to_second_layer = 0
		elif (self.layer2_moisture < self.Sat):
			self.R_to_second_layer = min((self.Sat - self.layer2_moisture) * self.SM2 * 1000,
			                             (self.SM1_before - self.FC) * self.SM1 * 1000 * self.daily_perc_factor)
		else:
			self.R_to_second_layer = 0
		self.SM2_before = (self.layer2_moisture * self.SM2 * 1000 + self.R_to_second_layer) / self.SM2 / 1000
	
	def secondary_runoff(self, day):
		"""

		"""
		if (((self.SM1_before * self.SM1 - self.R_to_second_layer / 1000) / self.SM1) > self.Sat):
			sec_run_off = (((
					                self.SM1_before * self.SM1 - self.R_to_second_layer / 1000) / self.SM1) - self.Sat) * self.SM1 * 1000
		else:
			sec_run_off = 0
		self.SM1_fraction = min((self.SM1_before * self.SM1 * 1000 - self.R_to_second_layer) / self.SM1 / 1000,
		                        self.Sat)
	
	def percolation_to_GW(self, day):
		"""

		"""
		self.budget.GW_rech.append(max((self.SM2_before - self.FC) * self.SM2 * self.daily_perc_factor * 1000, 0))
		self.layer2_moisture = min(((self.SM2_before * self.SM2 * 1000 - self.budget.GW_rech[day]) / self.SM2 / 1000),
		                           self.Sat)
