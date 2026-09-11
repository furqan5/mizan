within ;
model TowerBasin
  "Salt mass balance on a cooling-tower basin -- the dynamics the steady-state engine cannot see.

   WHY THIS MODEL EXISTS.

   src/controller.py is a steady-state optimiser: it asks what cycles of
   concentration a water can hold and prices the answer. It says nothing about
   HOW LONG the basin takes to get there. That matters, because a supervisory
   controller that changes the blowdown setpoint is changing a first-order
   system with a large time constant, and if that constant is comparable to
   the period over which conditions change then the setpoint is chasing a
   target it can never reach.

   The balance is exact and needs no correlation:

     d(V*c)/dt = M*c_m - (B + D)*c        salt
     V constant, M = E + B + D            water, level-controlled basin

   so   V dc/dt = (E + B + D)*c_m - (B + D)*c

   with steady state c/c_m = (E + B + D)/(B + D) = cycles, as expected, and a
   time constant tau = V/(B + D) -- the basin turnover time on the NON-
   evaporative losses only. Evaporation removes water but leaves the salt, so
   it does not appear in tau.
  "

  parameter Real V(unit="kg") = 50000 "Basin water inventory (50 m3)";
  parameter Real E(unit="kg/s") = 4.2 "Evaporation, set by the heat duty";
  parameter Real D(unit="kg/s") = 0.00478 "Drift, 1e-5 of 478 kg/s circulating";
  parameter Real c_m(unit="mg/kg") = 1500 "Makeup TDS";
  parameter Real cyc0 = 3.0 "Cycles held before the step";
  parameter Real cyc1 = 5.0 "Cycles demanded after the step";
  parameter Real t_step(unit="s") = 3600 "When the setpoint moves";

  // blowdown that holds a given cycles count, from the steady balance
  function bd_for = TowerBasin_bd;

  Real B(unit="kg/s") "Blowdown, the manipulated variable";
  Real c(unit="mg/kg", start = cyc0*c_m, fixed = true) "Basin TDS";
  Real cycles "c/c_m, what a conductivity controller reads";
  Real tau_h "Instantaneous time constant, hours";
  Real M(unit="kg/s") "Fresh makeup";

equation
  B = if time < t_step then E/(cyc0 - 1) else E/(cyc1 - 1);
  M = E + B + D;
  V * der(c) = M*c_m - (B + D)*c;
  cycles = c / c_m;
  tau_h = V / (B + D) / 3600;
  annotation(experiment(StartTime=0, StopTime=432000, Interval=600));
end TowerBasin;

function TowerBasin_bd
  input Real E; input Real cyc;
  output Real B;
algorithm
  B := E/(cyc - 1);
end TowerBasin_bd;
