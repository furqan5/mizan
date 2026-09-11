within ;
model TowerSilicaDynamics
  "Silica saturation in a tower basin, where the LIMIT moves faster than the CONCENTRATION can follow.

   WHY THIS MODEL EXISTS.

   The steady-state engine computes a silica ceiling and the controller holds
   the basin at it. Both treat the limit as fixed. It is not: amorphous silica
   is PROGRADE, so its solubility falls as the basin cools, and a tower basin
   cools every night.

     18 C -> 101 mg/L      30 C -> 130 mg/L
     22 C -> 110            34 C -> 140
     26 C -> 120            38 C -> 151

   So over a 10 K diurnal swing the CEILING itself moves by about 20 %, on a
   twelve-hour period. Meanwhile the basin concentration can only be changed
   by blowdown, and that has a time constant of V/(B+D) -- about thirteen
   hours on a 50 m3 basin at five cycles, established in TowerBasin.mo.

   TWO TIMESCALES, AND THEY ARE THE WRONG WAY ROUND. The limit moves on a
   half-day; the state that must respect it moves on half a week. A setpoint
   placed at the limit computed for MEAN conditions is therefore exceeded
   every night, and no blowdown policy can prevent it -- the water simply
   cannot be diluted fast enough.

   WHAT THIS MODEL PRODUCES: the margin. It runs the basin at a blowdown that
   holds the saturation ratio at exactly 1.0 at the mean basin temperature,
   then reports how far above 1.0 the ratio actually goes. That excursion is
   the setpoint margin a real supervisory controller must carry, and nothing
   in the steady-state engine computes it.

   Makeup silica is 18 mg/L -- MEASURED, from Table 1 of AlMajnouni & Jaffer,
   NACE Paper 577, Riyadh Refinery secondary treated sewage effluent. Not the
   26.8 mg/L previously imported from brackish groundwater.
  "

  constant Real pi = 3.141592653589793;

  // --- basin and duty ------------------------------------------------------
  parameter Real V(unit="kg") = 50000 "Basin water inventory, 50 m3";
  parameter Real E(unit="kg/s") = 4.2 "Evaporation, set by the heat duty";
  parameter Real D(unit="kg/s") = 0.00478 "Drift, 1e-5 of 478 kg/s";

  // --- makeup chemistry ----------------------------------------------------
  parameter Real c_m(unit="mg/kg") = 18.0
    "Makeup silica as SiO2 [C: NACE 577 Table 1, measured]";

  // --- diurnal basin temperature ------------------------------------------
  parameter Real T_mean(unit="degC") = 30.0 "Mean basin temperature";
  parameter Real T_amp(unit="K") = 5.0 "Half the diurnal swing";
  parameter Real t_peak(unit="s") = 54000 "Time of the daily maximum, 15:00";

  // --- the setpoint under test --------------------------------------------
  parameter Real SR_setpoint = 1.0
    "Saturation ratio the blowdown is sized to hold AT THE MEAN temperature";

  // --- van 't Hoff for amorphous silica, phreeqc.dat -----------------------
  //   SiO2(a) + 2H2O = H4SiO4 ;  log K(25 C) = -2.71 ; dH = +3.59 kcal/mol
  //   POSITIVE enthalpy -> solubility RISES with temperature (prograde)
  constant Real logK25 = -2.71;
  constant Real A_vh = 784.58 "dH/(2.303 R), kelvin";

  Real T_basin(unit="degC") "Basin temperature";
  Real S_sat(unit="mg/kg") "Amorphous silica solubility at T_basin";
  Real S_sat_mean(unit="mg/kg") "Solubility at the mean temperature";
  Real c(unit="mg/kg", start = 18.0 * 5.0, fixed = true) "Basin silica";
  Real SR "Saturation ratio, c/S_sat -- the quantity that must stay <= 1";
  Real cycles "c/c_m, what a conductivity controller reads";
  Real B(unit="kg/s") "Blowdown";
  Real c_target(unit="mg/kg") "Concentration the setpoint implies at T_mean";
  Real excursion "How far SR exceeds its setpoint. THIS IS THE OUTPUT.";

equation
  T_basin = T_mean - T_amp * cos(2 * pi * (time - t_peak) / 86400);

  S_sat = 60.084 * 1000 * 10 ^ (logK25 - A_vh * (1 / (T_basin + 273.15)
                                                 - 1 / 298.15));
  S_sat_mean = 60.084 * 1000 * 10 ^ (logK25 - A_vh * (1 / (T_mean + 273.15)
                                                      - 1 / 298.15));

  // Blowdown is FIXED, sized from the steady balance to hold the setpoint at
  // the mean temperature. That is exactly what a conductivity controller with
  // a fixed setpoint does, and the point of the model is that it is not
  // enough.
  c_target = SR_setpoint * S_sat_mean;
  B = E / (c_target / c_m - 1.0) - D;

  V * der(c) = (E + B + D) * c_m - (B + D) * c;

  SR = c / S_sat;
  cycles = c / c_m;
  excursion = SR - SR_setpoint;

  annotation(experiment(StartTime=0, StopTime=864000, Interval=600),
    Documentation(info="Run to steady periodic state, then read max(SR)."));
end TowerSilicaDynamics;
